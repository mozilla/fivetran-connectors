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

    products = bzapi.getproducts()

    products_data = [
        {"name": product["name"], "id": product["id"]} for product in products
    ]

    components_data = [
        {
            "name": component["name"],
            "id": component["id"],
            "default_qa_contact": component["default_qa_contact"],
            "is_active": component["is_active"],
            "description": component["description"],
        }
        for product in products
        for component in product["components"]
    ]

    since_id = None
    if "since_id" in request.json["state"]:
        since_id = request.json["state"]["since_id"]

    if since_id is None:
        # limit the max. of data to be queried
        since_id = config["max_date"]

    offset = 0
    if "offset" in request.json["state"]["offset"]:
        offset = request.json["state"]["offset"]

    sorted_products = sorted([product["name"] for product in products_data])
    sorted_components = sorted([component["name"] for component in components_data])
    query = bzapi.build_query(
        product=sorted_products,
        component=sorted_components,
        limit=config["bug_limit"],
        offset=offset,
    )
    query["last_change_time"] = since_id

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

    hasMore = len(bugs) == config["bug_limit"]
    state = {"since_id": since_id, "offset": offset + 1}

    schema = {
        "products": {
            "primary_key": ["id", "name"],
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
        "hasMore": hasMore,
    }
