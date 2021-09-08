import json
from typing import Any, Dict

import requests


def main(request):
    """
    Function to execute.

    The standard format of `request` is a JSON object with the following fields:
        `agent`: informal object
        `state`: contains bookmark that marks the data Fivetran has already synced
        `secret`: optional JSON object that contains access keys or API keys
    """
    # add custom connector code
    pass


def response(
    state: Dict[str, Any],
    schema: Dict[Any, Any],
    inserts: Dict[Any, Any] = {},
    deletes: Dict[Any, Any] = {},
    hasMore: bool = False,
):
    """Creates the response JSON object that will be processed by Fivetran."""
    return {
        "state": state,
        "schema": schema,
        "insert": inserts,
        "delete": deletes,
        "hasMore": hasMore,
    }
