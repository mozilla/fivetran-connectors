import os
import shutil
from pathlib import Path
from typing import Dict, List

import click
import jinja2

ROOT_DIR = (Path(__file__).parent / "..").resolve()
TEMPLATES_DIR = ROOT_DIR / "tools" / "templates"
CONNECTOR_DIR = ROOT_DIR / "connectors"

def copy_connector_template(connector_name: str):
    """Copy job template files to jobs directory."""
    try:
        new_dir = shutil.copytree(
            src=TEMPLATES_DIR,
            dst=CONNECTOR_DIR / connector_name.replace("-", "_"),
        )
    except FileExistsError:
        raise ValueError(f"Connector with name {connector_name} already exists.")


@click.command()
@click.argument("connector_name")
def create_connector(connector_name: str):
    copy_connector_template(connector_name)

if __name__ == "__main__":
    create_connector()
