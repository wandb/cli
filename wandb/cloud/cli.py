import click
from click.exceptions import ClickException
from wandb.cli import cli, display_error, api as wandb_api
from wandb.cloud import api
from wandb import wandb_dir
from distutils.spawn import find_executable
from six.moves.configparser import ConfigParser


class CloudGroup(click.Group):
    @display_error
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            # TODO: allow the --help command without kubectl
            if find_executable("kubectl") is None:
                raise ClickException(
                    "kubectl is required for `wandb cloud` commands, install it here: https://goo.gl/T6VqiB")
            return rv

        return None


@cli.group(cls=CloudGroup)
def cloud():
    """Manage kubernetes clusters for remote execution

Examples:

    wandb cloud run train.py
    wandb cloud ssh run_id
    wandb cloud status run_id
    wandb cloud status
    wandb cloud top
    wandb cloud cleanup
    """
    pass


# TODO: We will likely need an approach like: https://blog.konpat.me/pythons-pseudo-terminal-pty-examples/
@cloud.command(help="Connect to a currently running container or failed process")
@click.argument("run_id")
@display_error
def ssh(run_id):
    api.kubectl(["exec", "-it",
                 "run-%s" % run_id, "/bin/sh"], tty=True)


@cloud.command(help="Run a script in the cluster")
@click.argument("command")
@click.option("--image", help="The docker image to use")
@display_error
def run(command, image=None):
    if not wandb_api.git.enabled:
        raise ClickException(
            "run can only be run from within git repositories.")
    click.echo("\U0001F680 script in the \u26C5")
    run_id = api.launch_run(command, image=image)


@cloud.command(help="Enable the container to use your ssh key for git checkouts")
@click.option("--host", help="The host to ssh to", default="github.com")
@click.option("--key", help="The path to ssh key", default="~/.ssh/id_rsa")
@display_error
def enable_ssh(host, key):
    api.store_ssh(key=key)
    config = ConfigParser()
    settings = wandb_dir() + "/settings"
    config.read(settings)
    config.set("default", "ssh_enabled", "true")
    with open(settings, "w") as f:
        config.write(f)
    click.echo("SSH enabled!")


@cloud.command(help="Get the status of a run")
@click.argument("run_id", nargs=-1)
@display_error
def status(run_id=None):
    res = api.kubectl(api.pod(run_id) if run_id else api.pods(), to_json=True)
    if len(res["items"]) == 0:
        click.echo("No pods are running in the wandb namespace")
    else:
        for item in res["items"]:
            phase = item["metadata"]["name"] + \
                " (" + item["status"]["phase"] + ")"
            click.echo(click.style(phase + ":", bold=True))
            messaged = False
            for c in item["status"]["conditions"]:
                if c.get('message'):
                    messaged = True
                    click.echo("  " + c['message'])
            if not messaged or run_id:
                click.echo(api.kubectl(
                    ["describe", "pod", item["metadata"]["name"]]).split("Events:")[-1])
                # res = api.logs(item["metadata"]["name"])
                # click.echo("\t" + res)


@cloud.command(help="Get the logs of a run")
@click.argument("run_id")
@display_error
def logs(run_id=None):
    api.logs(run_id)


@cloud.command(help="Kill a run")
@click.argument("run_id")
@display_error
def kill(run_id=None):
    api.delete(run_id)


@cloud.command(help="Remove stale resources")
@display_error
def cleanup():
    res = [pod["metadata"]["name"] for pod in api.kubectl(api.pods(), to_json=True)[
        "items"] if pod["status"]["phase"] in ["Pending", "Completed", "Failed"]]
    if click.confirm("About to delete %s, ok? " % res):
        for run in res:
            api.kubectl(["delete", "pod", run])


@cloud.command()
@click.argument("run_id")
@display_error
def events(run_id):
    api.events(run_id)
