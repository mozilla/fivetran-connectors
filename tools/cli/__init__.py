"""Fivetran connectors CLI."""

import click

from .._version import __version__
from ..connector import connector
from ..ci_config import ci_config


def cli(prog_name=None):
    """Create the Fivetran CLI."""
    commands = {
        "connector": connector,
        "ci_config": ci_config,
    }

    @click.group(commands=commands)
    @click.version_option(version=__version__)
    def group():
        """CLI tools for working with fivetran."""
        pass

    group(prog_name=prog_name)


if __name__ == "__main__":
    cli()
