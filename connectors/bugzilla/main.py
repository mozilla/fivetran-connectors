from typing import Any, Dict

import bugzilla


def main(request):
    """
    Function to execute.

    The standard format of `request` is a JSON object with the following fields:
        `agent`: informal object
        `state`: contains bookmark that marks the data Fivetran has already synced
        `secret`: optional JSON object that contains access keys or API keys, other config
    """
    config = request.json["secret"]

    bzapi = bugzilla.Bugzilla(config["url"], api_key=config["api_key"])

    if not bzapi.logged_in:
        raise ValueError("Could not connect to Bugzilla.")

    components = [
        component
        for product in config["products"]
        for component in bzapi.getcomponents(product)
    ]

    return response("", {}, components, hasMore=False)


def response(
    since_id: str, schema: Dict[Any, Any], inserts: Dict[Any, Any], hasMore: bool
):
    """Creates the response JSON object that will be processed by Fivetran."""
    return {
        "state": {since_id: since_id},
        "schema": schema,
        "insert": inserts,
        "hasMore": hasMore,
    }
