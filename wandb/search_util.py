"""
Helper functions and classe for the hyperparameter search prototype code
which Adro wrote.
"""

import random

class Sampler:
    """
    Returns unique samples from a mixed discrete / coninuous distribution.
    """

    def __init__(self, axes):
        """
        Axes is a dictionary of labeled axes which are either continuous:

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
        self._axes = {}
        self._n_elements = 1
        for label, data in axes.items():
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

        # take some samples from this setup
        print("num elements:", self._n_elements)
        for x in range(33):
            print(self.sample())
        import sys
        sys.exit(-1)

    def sample(self):
        """Draw a unique sample from this sampler."""
        if len(self._drawn_samples) == self._n_elements:
            raise RuntimeError('No more unique elements to sample.')
        draw = lambda: tuple(sorted(
            [(label, f()) for (label, f) in self._axes.items()]))
        sample = draw()
        while sample in self._drawn_samples:
            sample = draw()
        self._drawn_samples.add(sample)
        return sample

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
