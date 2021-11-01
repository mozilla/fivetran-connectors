import shutil
from pathlib import Path

import click
import jinja2

ROOT_DIR = (Path(__file__).parent / "..").resolve()
TEMPLATES_DIR = ROOT_DIR / "tools" / "templates"
CONNECTOR_DIR = ROOT_DIR / "connectors"
CI_WORKFLOW_TEMPLATE_NAME = "ci_workflow.yaml"


def copy_connector_template(connector_name: str, destination: str):
    """Copy job template files to jobs directory."""
    try:
        shutil.copytree(
            src=TEMPLATES_DIR,
            dst=Path(destination) / connector_name,
        )
    except FileExistsError:
        raise ValueError(f"Connector with name {connector_name} already exists.")

    # generate CI config for connector
    template_loader = jinja2.FileSystemLoader(TEMPLATES_DIR)
    template_env = jinja2.Environment(loader=template_loader)

    try:
        ci_workflow_template = template_env.get_template(CI_WORKFLOW_TEMPLATE_NAME)
    except jinja2.exceptions.TemplateNotFound:
        raise FileNotFoundError(
            f"{CI_WORKFLOW_TEMPLATE_NAME} must be in {TEMPLATES_DIR}"
        )

    ci_workflow_text = ci_workflow_template.render(connector_name=connector_name)
    with open(Path(destination) / connector_name / CI_WORKFLOW_TEMPLATE_NAME, "w") as f:
        f.write(ci_workflow_text)


@click.group(help="Commands for managing connectors.")
def connector():
    """Create the CLI group for the connector command."""
    pass


@connector.command(help="""Create a new custom Fivetran connector.""")
@click.argument("connector_name")
@click.option(
    "--destination", "-d", help="Destination directory", default=CONNECTOR_DIR
)
def create(connector_name: str, destination: str):
    copy_connector_template(connector_name, destination)
