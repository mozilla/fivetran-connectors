import bugzilla
import json
import requests

from typing import Any, Dict

def main(request):
    """
    Function to execute.
    
    The standard format of `request` is a JSON object with the following fields:
        `agent`: informal object
        `state`: contains bookmark that marks the data Fivetran has already synced
        `secret`: optional JSON object that contains access keys or API keys, other config
    """
    config = request["secret"]

    bzapi = bugzilla.Bugzilla(config["url"], api_key=config["api_key"])

    if not bzapi.logged_in:
        raise ValueError("Could not connect to Bugzilla.")

    bzapi = bugzilla.Bugzilla(config["url"], api_key=config["api_key"])
    data = {"components": bzapi.getcomponents(config["product"])}

    return response()



def response(since_id: str, schema: Dict[Any], inserts: Dict[Any], hasMore: bool):
    """Creates the response JSON object that will be processed by Fivetran."""
    return {
        "state": {
            since_id: since_id
        },
        "schema": schema,
        "insert": inserts,
        "hasMore": hasMore
    }
