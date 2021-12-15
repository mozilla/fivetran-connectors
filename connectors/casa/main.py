import logging
from typing import Any, Dict

import requests

logging.basicConfig(
    format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
)

SCHEMA = {
    "projects": {"primary_key": ["id"]},
    "users": {"primary_key": ["id"]},
}

QUERY_RESULT_LIMIT = 100

CASA_URL = "https://biztera.com/api/v1"
PROJECTS_URL = f"{CASA_URL}/projects"
USERS_URL = f"{CASA_URL}/users"


def main(request):
    """
    Function to execute.

    The standard format of `request` is a JSON object with the following fields:
        `agent`: informal object
        `state`: contains bookmark that marks the data Fivetran has already synced
        `secrets`: optional JSON object that contains access keys or API keys, other config
                   access_token: <access_token>
    """

    config = request.json.get("secrets", {})
    state = request.json.get("state", {})

    logging.info(f"Received Fivetran request with state: {state}")

    access_token = config["access_token"]

    fetch_more_projects = state.get("fetch_more_projects", True)
    fetch_more_users = state.get("fetch_more_users", True)
    users_offset = state.get("users_offset", 0)
    projects_offset = state.get("projects_offset", 0)

    def _fetch(offset, url):
        logging.info(f"Sending request to {url} with offset: {offset}")
        request_params = {
            "limit": QUERY_RESULT_LIMIT,
            "offset": offset,
        }

        headers = {"Authorization": f"Bearer {access_token}"}

        http_response = requests.get(url=url, params=request_params, headers=headers)

        if http_response.status_code != 200:
            raise Exception(
                f"Error connecting to Biztera API (url: {url}). Response: {http_response}"
            )

        results = http_response.json()
        if "data" in results:
            results = results["data"]

        if len(results) == QUERY_RESULT_LIMIT:
            fetch_more = True
            new_offset = offset + QUERY_RESULT_LIMIT
        else:
            fetch_more = False
            new_offset = 0

        return results, fetch_more, new_offset

    if fetch_more_projects:
        projects, new_fetch_more_projects, new_projects_offset = _fetch(
            projects_offset, PROJECTS_URL
        )
    else:
        projects = []
        new_fetch_more_projects = False
        new_projects_offset = 0

    if fetch_more_users:
        users, new_fetch_more_users, new_users_offset = _fetch(users_offset, USERS_URL)
    else:
        users = []
        new_fetch_more_users = False
        new_users_offset = 0

    has_more = new_fetch_more_users or new_fetch_more_projects

    # Reset state for next sync
    if not has_more:
        new_fetch_more_projects = True
        new_fetch_more_users = True
        new_projects_offset = 0
        new_users_offset = 0

    new_state = {
        "fetch_more_users": new_fetch_more_users,
        "fetch_more_projects": new_fetch_more_projects,
        "users_offset": new_users_offset,
        "projects_offset": new_projects_offset,
    }

    logging.info(
        f"Updated state: {new_state}, hasMore: {has_more}, inserting {len(users)} users and {len(projects)} projects."
    )

    return response(
        state=new_state,
        schema=SCHEMA,
        inserts={"users": users, "projects": projects},
        deletes={},
        hasMore=has_more,
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
