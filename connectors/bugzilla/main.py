from datetime import datetime
from typing import Any, Dict

import bugzilla


def main(request):
    """
    Function to execute.

    The standard format of `request` is a JSON object with the following fields:
        `agent`: informal object
        `state`: contains bookmark that marks the data Fivetran has already synced
        `secrets`: optional JSON object that contains access keys or API keys, other config
    """
    # authenticate to Bugzilla API
    config = request.json["secrets"]
    bzapi = bugzilla.Bugzilla(config["url"], api_key=config["api_key"])

    if not bzapi.logged_in:
        raise ValueError("Could not connect to Bugzilla.")

    # get product data
    products_data = [
        {"name": product} for product in config["products"]
    ]

    # get component data
    products = config["products"]
    components_data = [
        {
            "name": component["name"],
            "id": component["id"],
            "default_qa_contact": component["default_qa_contact"],
            "is_active": component["is_active"],
            "description": component["description"],
        }
        for product in products
        for _, component in bzapi.getcomponentsdetails(product).items()
    ]

    # since_id is based on the last date the import ran
    # only fetch bugs that have been updated since then
    since_id = None
    if "since_id" in request.json["state"]:
        since_id = request.json["state"]["since_id"]

    if since_id is None:
        # if this is the first time the connector is executed
        # limit the max. of data to be queried
        since_id = config["max_date"]

    # check if the invokation happened because a previous run indicated
    # that there is more data available
    offset = 1
    if "offset" in request.json["state"]:
        offset = request.json["state"]["offset"]

    # query bugs from all available products and components
    # sort product and component names to ensure the same query is executed in 
    # subsequent runs
    sorted_products = sorted([product["name"] for product in products_data])
    sorted_components = sorted([component["name"] for component in components_data])
    query = bzapi.build_query(
        product=sorted_products,
        component=sorted_components,
        limit=config["bug_limit"]
    )
    query["last_change_time"] = since_id
    query["offset"] = offset

    bugs = bzapi.query(query)

    bug_data = [
        {
            "id": bug.id,
            "summary": bug.summary,
            "assigned_to": bug.assigned_to,
            "creation_time": bug.creation_time,
            "status": bug.status,
            "last_change_time": bug.last_change_time,
            "creator": bug.creator,
            "product": bug.product,
            "component": bug.component,
        }
        for bug in bugs
    ]

    # check if there is more data
    if len(bugs) == config["bug_limit"]:
        hasMore = True
    else:
        hasMore = False
        since_id = datetime.now().strftime("%Y-%m-%dT%H-%M-%SZ")

    state = {"since_id": since_id, "offset": offset + 1}

    schema = {
        "products": {
            "primary_key": ["name"],
        },
        "components": {"primary_key": ["id", "name"]},
        "bugs": {"primary_key": ["id"]},
    }

    return response(
        state,
        schema=schema,
        inserts={
            "products": products_data,
            "components": components_data,
            "bugs": bug_data,
        },
        hasMore=hasMore,
    )


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
