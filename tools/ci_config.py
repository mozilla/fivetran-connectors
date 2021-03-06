import os
import sys
from pathlib import Path

import click
import jinja2
import yaml
from yaml.scanner import ScannerError

ROOT_DIR = (Path(__file__).parent / "..").resolve()
CI_CONFIG_TEMPLATE = "config.template.yml"
CI_WORKFLOW_TEMPLATE_NAME = "ci_workflow.yaml"
DEPLOY_CONFIG = "deploy.yaml"
CONNECTORS_DIR = "connectors"

CI_CONFIG_HEADER = """###
# This config.yml was generated by tools/ci_config.py.
# Changes should be made to templates/config.template.yml and re-generated.
###"""


class DeployConfig:
    def __init__(self, file):
        # parse deploy configs from file
        with open(file) as f:
            self.config = yaml.safe_load(f)
    
    def to_dict(self):
        config = []
        for (connector_name, connector_config) in self.config.items():
            config.append(
                {
                    "connector_name": connector_name,
                    "connector": connector_config['connector'],
                    "environment": connector_config['environment']
                }
            )

        return config


def validate_yaml(yaml_path: Path) -> bool:
    """Load a yaml file and return the success of the parse."""
    with open(yaml_path) as f:
        try:
            yaml.safe_load(f)
        except ScannerError:
            return False
    return True


def update_config(dry_run: bool = False, root: str = ROOT_DIR) -> str:
    """Collect job and workflow configs per job and create new config."""
    root_dir = Path(root)
    ci_dir = root_dir / ".circleci"
    template_loader = jinja2.FileSystemLoader(ci_dir)
    template_env = jinja2.Environment(loader=template_loader)
    config_template = template_env.get_template("config.template.yml")

    connector_dir = root_dir / CONNECTORS_DIR
    deploy_config = DeployConfig(root_dir / DEPLOY_CONFIG)

    workflow_configs = sorted(
        [
            obj
            for obj in connector_dir.glob(f"*/{CI_WORKFLOW_TEMPLATE_NAME}")
            if obj.is_file()
        ]
    )
    connectors = [
        os.path.basename(f.path) for f in os.scandir(connector_dir) if f.is_dir()
    ]

    invalid_configs = [
        str(conf.relative_to(root_dir))
        for conf in workflow_configs
        if not validate_yaml(conf)
    ]
    if len(invalid_configs) > 0:
        print("Error: Invalid CI configs", file=sys.stderr)
        print("\n".join(invalid_configs), file=sys.stderr)
        sys.exit(1)

    config_text = config_template.render(
        config_header=CI_CONFIG_HEADER,
        workflows="\n".join(
            [file_path.read_text() for file_path in workflow_configs]
        ),
        connectors=connectors,
        deployments=deploy_config.to_dict(),
    )

    if dry_run:
        print(config_text)
    else:
        with open(root_dir / ".circleci" / "config.yml", "w") as f:
            f.write(config_text)

    return config_text


@click.group(help="Commands for managing CI configuration.")
def ci_config():
    """Create the CLI group for the ci command."""
    pass


@ci_config.command(help="""Update CI configuration.""")
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="Dry run will print to stdout instead of overwriting config.yml",
)
@click.option("--root", "-r", help="Root directory", default=ROOT_DIR)
def update(dry_run: bool, root: str):
    update_config(dry_run, root)
