"""
Helper functions and classe for the hyperparameter search prototype code
which Adro wrote.
"""

import copy
import json
import os
import random
import re
import subprocess
import threading
import uuid
import yaml

from wandb import wandb_run
from wandb import api as wandb_api
from wandb import util

class Sampler:
    """
    Returns unique samples from a mixed discrete / coninuous distribution.
    """

    class NoMoreSamples(Exception):
        """
        Thrown by the sample() method when all samples have been exhausted.
        """
        pass

    def __init__(self, config):
        """
        Config is the wandb config yaml file but parameters are generalized
        as follows. Axes can be continuous:

            <axis name>: {
                min: <float>,
                max: <float>,
                type: 'linear' (defualt) | 'logarithmic'
            }

        or discrete:

            <axis name>: {min: <int>, max: <int>}

        or a discrete choice of values

            <axis name>: { values: ['value1', 'value2', ...]}

        The axis type is determined automatically.
        """
        # Parse the axes into our own, more explicit axes data structure.
        self._config = copy.copy(config)
        self._axes = {}
        self._n_elements = 1
        for label, data in config.items():
            # All axes must be defined as dictionaries.
            if type(data) != dict:
                continue

            # Either a integer or floating point scale.
            elif {'min', 'max'} < data.keys():
                min, max = data['min'], data['max']

                # floating point scale
                if type(min) == type(max) == float:

                    # logarithmic scale
                    if ('type', 'logarithmic') in data.items():
                        self._axes[label] = Sampler._log_range_axis(min, max)
                        self._n_elements = float('inf')

                    # linear scale
                    else:
                        self._axes[label] = Sampler._linear_range_axis(min, max)
                        self._n_elements = float('inf')

                # integer range
                elif type(min) == type(max) == int:
                    assert min <= max
                    self._axes[label] = Sampler._set_axis(range(min, max+1))
                    self._n_elements *= max - min + 1

            # a discrete set of values
            elif 'values' in data:
                self._axes[label] = Sampler._set_axis(data['values'])
                self._n_elements *= len(data['values'])

            # a single value
            elif 'value' in data:
                self._axes[label] = Sampler._set_axis([data['value']])

        # remember previous samples to make sure samples are unique
        self._drawn_samples = set()

    def sample(self):
        """Draw a unique sample from this sampler."""
        # Don't sample the same point twice.
        if len(self._drawn_samples) == self._n_elements:
            raise Sampler.NoMoreSamples

        # Draw a unique sample
        draw = lambda: tuple(sorted(
            [(label, f()) for (label, f) in self._axes.items()]))
        sample = draw()
        while sample in self._drawn_samples:
            sample = draw()
        self._drawn_samples.add(sample)

        # Apply it to the config file
        config = copy.copy(self._config)
        for key, value in sample:
            config[key]['value'] = value
        return config

    @staticmethod
    def _linear_range_axis(min, max):
        """Uniform distribution on [min, max]."""
        assert min <= max, "Range must be nonempty."
        return lambda: random.uniform(min,max)

    @staticmethod
    def _log_range_axis(min, max):
        """Logarithic distribution on [min,max]."""
        assert min <= max, "Range must be nonempty."
        raise NotImplementedError('Logarithmic ranges not implemented.')

    @staticmethod
    def _set_axis(values):
        """Samples from a finite set of values."""
        return lambda: random.choice(values)

def run_wandb_subprocess(program, config):
    """Runs wandb in a subprocess, returning the ???

    config - the yaml configuration to use
    """
    # create a uid and unique filenames to store data
    uid = wandb_run.generate_id()
    path = wandb_run.run_dir_path(uid, dry=False)
    util.mkdir_exists_ok(path)
    config_filename = os.path.join(path, 'cofig_search_template.yaml')
    proc_stdout = open(os.path.join(path, 'stdout'), 'wb')
    proc_stderr = open(os.path.join(path, 'stderr'), 'wb')

    # write the temporary config file, then run the command
    with open(config_filename, 'w') as config_stream:
        yaml.dump(config, config_stream, default_flow_style=False)
    print('Created temporary config %s.' % config_filename)
    cmd = ['wandb', 'run', '--configs', config_filename, '--id', uid, program]
    print('Running "%s".' % ' '.join(cmd))
    proc = subprocess.Popen(cmd, stdout=proc_stdout, stderr=proc_stderr)
    return (uid, proc)

def query_runs(uids):
    """
    Gets the following information the runs with specified ids = [id1, id2, ...]
    {
        id1: {
            'state': <string>,
            'val_loss_history': <list of float>,
            'summary_val_loss': <float>
            }
        id2: ...
    }
    """
    # Load the results into a dictionary
    results = { uid :
        {
            'state': 'not_started',
            'val_loss_history': [],
            'summary_val_loss': float('inf')
        } for uid in uids }

    # Query by parsing the filesystem.
    # TODO: Do this by reading from the website.
    wandb_path = 'wandb'
    wandb_history = 'wandb-history.jsonl'
    run_paths = os.listdir(wandb_path)
    for uid in uids:
        # figure out the path for this run
        print('uid:', uid)
        path_filter = re.compile('run-\d{8,8}_\d{6,6}-%s' % uid)
        run_path = max(filter(path_filter.match, run_paths))

        # parse the runfile
        history_path = os.path.join(wandb_path, run_path, wandb_history)
        try:
            with open(history_path) as history:
                 results[uid]['val_loss_history'] = [json.loads(line)['val_loss']
                    for line in history.readlines()]
        except FileNotFoundError:
            pass

    # Run a gql query to get this rest of the data.
    # TODO: Eventually, all data should come this way, but I was having trouble
    # adding `history` to this query.
    api = wandb_api.Api()
    project = api.settings()['project']
    for run in api.list_runs(project):
        uid = run['name'].strip()
        if uid in uids:
            try:
                results[uid]['state'] = run['state']
                results[uid]['summary_val_loss'] = \
                    json.loads(run['summaryMetrics'])['val_loss']
            except KeyError:
                pass

    # All done
    return results
