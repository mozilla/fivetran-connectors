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
    projects_bookmark = state.get("projects_bookmark")

    def _fetch(url, request_params=None):
        request_params = request_params or {}
        request_params["limit"] = QUERY_RESULT_LIMIT

        logging.info(f"Sending request to {url} with params: {request_params}")

        headers = {"Authorization": f"Bearer {access_token}"}

        http_response = requests.get(url=url, params=request_params, headers=headers)

        if http_response.status_code != 200:
            raise Exception(
                f"Error connecting to Biztera API (url: {url}). Response: {http_response}"
            )

        return http_response.json()

    projects = []
    new_fetch_more_projects = False
    new_projects_bookmark = None

    if fetch_more_projects:
        if projects_bookmark is not None:
            projects_response = _fetch(
                PROJECTS_URL, request_params={"bookmark": projects_bookmark}
            )
        else:
            projects_response = _fetch(PROJECTS_URL)

        projects = projects_response["data"]
        metadata = projects_response["metadata"]

        if "nextPage" in metadata:
            new_projects_bookmark = metadata["nextPage"]["bookmark"]
            new_fetch_more_projects = True

    users = []
    new_fetch_more_users = False
    new_users_offset = 0

    if fetch_more_users:
        users = _fetch(USERS_URL, request_params={"offset": users_offset})
        if len(users) == QUERY_RESULT_LIMIT:
            new_fetch_more_users = True
            new_users_offset = users_offset + QUERY_RESULT_LIMIT

    has_more = new_fetch_more_users or new_fetch_more_projects

    # Reset state for next sync
    if not has_more:
        new_fetch_more_projects = True
        new_fetch_more_users = True
        new_projects_bookmark = None
        new_users_offset = 0

    new_state = {
        "fetch_more_users": new_fetch_more_users,
        "fetch_more_projects": new_fetch_more_projects,
        "users_offset": new_users_offset,
        "projects_bookmark": new_projects_bookmark,
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
