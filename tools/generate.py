import os
import shutil
from pathlib import Path
from typing import Dict, List

import click
import jinja2

ROOT_DIR = (Path(__file__).parent / "..").resolve()
TEMPLATES_DIR = ROOT_DIR / "tools" / "templates"
CONNECTOR_DIR = ROOT_DIR / "connectors"
CI_WORKFLOW_TEMPLATE_NAME = "ci_workflow.yaml"


def copy_connector_template(connector_name: str):
    """Copy job template files to jobs directory."""
    try:
        shutil.copytree(
            src=TEMPLATES_DIR,
            dst=CONNECTOR_DIR / connector_name.replace("-", "_"),
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
    with open(CONNECTOR_DIR / connector_name / CI_WORKFLOW_TEMPLATE_NAME, "w") as f:
        f.write(ci_workflow_text)


@click.command()
@click.argument("connector_name")
def create_connector(connector_name: str):
    copy_connector_template(connector_name)


if __name__ == "__main__":
    create_connector()
