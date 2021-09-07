import json
import requests

from typing import Any, Dict


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


def response(since_id: str, schema: Dict[Any], inserts: Dict[Any], hasMore: bool):
    """Creates the response JSON object that will be processed by Fivetran."""
    return {
        "state": {since_id: since_id},
        "schema": schema,
        "insert": inserts,
        "hasMore": hasMore,
    }
