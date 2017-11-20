from subprocess import run, Popen, PIPE
from kubernetes import client, config, watch
from kubernetes.stream import stream, ws_client
import pty
import signal
from wandb import termlog
from wandb import Error
import json
import os
import sys
from wandb.api import Api
from six import BytesIO
from wandb.wandb_run import generate_id
from jinja2 import Environment, FileSystemLoader, Template
import logging
import time
import click
import re
logger = logging.getLogger('wandb cloud')

PATH = os.path.abspath(os.path.dirname(__file__))
ENV = Environment(loader=FileSystemLoader(PATH + '/templates'))
DEFAULT_RUN_TYPE = "training"
DEFAULT_IMAGE = "us.gcr.io/playground-111/keras:tk"
api = Api()
config.load_kube_config()


def kubectl(args, stdin=False, tty=False, path=None, to_json=False, streamed=False):
    cmd = ["kubectl"] + args + ["-n", "wandb"]
    if path:
        cmd.extend(["-o", "jsonpath='{%s}'" % path])
    if to_json:
        cmd.extend(["-o", "json"])
    if stdin:
        cmd.extend(["-f", "-"])
    if os.getenv("DEBUG"):
        print("\U0001F913: %s" % ' '.join(cmd))
    if tty:
        return pty.spawn(cmd)
    elif stdin:
        res = Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    else:
        res = Popen(cmd, stdout=PIPE, stderr=PIPE)
    # TODO: sometimes kubectl fails with a 0 return code
    if res.returncode == 0:
        raise Error(res.stderr)
    if not stdin:
        err = res.stderr.read()
        if err:
            raise Error(err.decode("utf8"))
    elif tty or stdin:
        return res
    if streamed:
        output = res.stdout
        for char in iter(lambda: res.stdout.read(1), ''):
            streamed(char.decode("utf8"))
    else:
        output = res.stdout.read().decode("utf8") or res.stderr.read().decode("utf8")
    if to_json:
        try:
            res = json.loads(output)
        except json.decoder.JSONDecodeError:
            res = {"error": output}
        return res
    else:
        return output


def default_props():
    patch = BytesIO()
    if api.git.dirty:
        api.git.repo.git.execute(['git', 'diff'], output_stream=patch)
        patch.seek(0)
    cwd = "."
    if api.git.enabled:
        cwd = cwd + os.getcwd().replace(api.git.repo.working_dir, "")
    return {
        "project": api.settings('project'),
        "entity": api.settings('entity'),
        "run_id": generate_id(),
        "api_key": api.api_key,
        "patch": patch.read().decode("utf8"),
        "cwd": cwd,
        "run_type": DEFAULT_RUN_TYPE,
        "base_url": "https://api.wandb.ai",
        "image": DEFAULT_IMAGE,  # TODO: make this a public default image
        "gluster_enabled": False,
        "ssh_enabled": api.settings('ssh_enabled'),
        "source_run_id": None,
        "decription": None,
        "datasets": None,
        # TODO: support HTTPS?
        "repo": api.git.remote_url,
        "rev": "HEAD"
    }


def join_templates(*args):
    templates = "\n---\n".join(args)
    if os.getenv("DEBUG"):
        with open("wandb/k8s.yaml", "w") as f:
            f.write(templates)
    result = bytearray(templates, "utf8")
    return result


def pods(*args):
    return ["get", "pods"] + list(args)


def pod(run_id, *args):
    return pods("--selector=run_id=%s" % run_id, *args)


def pod_id(run_id):
    return kubectl(pods(run_id), path=".items[0].metadata.name")


def logs(run_id):
    time.sleep(2)
    click.echo(click.style("info", fg="blue", bold=True) + ": Connecting to your containers output...")
    v1 = client.CoreV1Api()
    w = watch.Watch()
    # TODO: likely changes to stream API: https://github.com/kubernetes-incubator/client-python/issues/199
    for e in v1.read_namespaced_pod_log("run-%s" % run_id, "wandb", follow=True, _preload_content=False):
        sys.stdout.write(e.decode("utf8"))
        sys.stdout.flush()
    return True


def delete(run_id):
    return kubectl(["delete", "pod", "run-%s" % run_id])


def store_ssh(host="github.com", key="~/.ssh/id_rsa"):
    res = Popen(["ssh-keyscan", host, ">", "/tmp/known_hosts"],
                stdout=PIPE, stderr=PIPE)
    if res.returncode == 0:
        raise Error(res.stderr)
    if not os.path.exists(os.path.expanduser(key)):
        raise Error("Can't find ssh key: %s" % key)
    res = kubectl(["create", "secret", "generic", "git-creds", "--from-file=ssh=%s" %
                   os.path.expanduser(key), "--from-file=known_hosts=/tmp/known_hosts"])
    print(res)


def kill_me_now(run_id):
    if click.confirm("Should we kill the process in the cluster?"):
        kubectl(["delete", "pod", "run-%s" % ])


def launch_run(command, run_type=DEFAULT_RUN_TYPE, image=DEFAULT_IMAGE, source_run_id=None, description=None):
    run_template = ENV.get_template("runner.yaml.j2")
    overrides = {
        "type": run_type,
        "command": command,
        "source_run_id": source_run_id,
        "description": description,
        "image": image
    }
    props = default_props()
    props.update(overrides)
    config_yaml = open(PATH + "/templates/config.yaml").read()
    run_yaml = run_template.render(props=props)
    cmd = kubectl(["apply"], stdin=True)
    result = cmd.communicate(input=join_templates(config_yaml, run_yaml))

    def signal_handler(signal, frame):
        kill_me_now(props['run_id'])
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    _events(props['run_id'])
    # TODO: Check failure
    kill_me_now(props['run_id'])
    return props['run_id']


def _format(ob, level="Normal", run_id=None):
    line = ""
    swap_log = None
    if level == "Warning":
        line = click.style("warn", fg="yellow", bold=True) + ": " + ob.message
    else:
        line = click.style("info", fg="blue", bold=True) + ": " + ob.message
        container = re.match(r".+\{(.+)\}", str(ob.involved_object.field_path))
        if container:
            line += " (%s)" % container.group(1)
            if container.group(1) != "git-sync" and ob.message == "Started container":
                swap_log = ob.involved_object.name.split("-")[-1]
    return line.replace('\n', ' '), swap_log


def _events(run_id):
    v1 = client.CoreV1Api()
    w = watch.Watch()
    last_line = ""
    swap_log = None
    for e in w.stream(v1.list_namespaced_event, "wandb"):
        if e['object'].metadata.name.startswith("run-%s" % run_id):
            level = e['object'].type
            next_line, swap_log = _format(
                e['object'], level=level, run_id=run_id)
            if swap_log:
                logs(swap_log)
                w.stop()
            elif last_line != next_line:
                last_line = next_line
                sys.stdout.write(last_line + "\n")
                sys.stdout.flush()
