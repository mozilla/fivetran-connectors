from dataclasses import dataclass
from typing import Union
from unittest import mock

import pytest
from casa.main import QUERY_RESULT_LIMIT, main


@dataclass
class MockResponse:
    json_data: Union[dict, list]
    status_code: int

    def json(self):
        return self.json_data


@dataclass
class FivetranRequest:
    json: dict


class TestMain:
    @mock.patch("casa.main.requests.get")
    def test_exception_if_unable_to_connect(self, mock_get):
        state = {}
        mock_get.return_value = MockResponse(json_data={}, status_code=401)
        fivetran_request = FivetranRequest(
            json={"secrets": {"access_token": "invalid_key"}, "state": state}
        )
        with pytest.raises(Exception):
            main(fivetran_request)

    @mock.patch("casa.main.requests.get")
    def test_should_get_more_users_and_projects_null_state(self, mock_get):
        state = {}
        valid_projects = {
            "data": [{"id": i, "name": f"project_{i}"} for i in range(100)]
        }
        valid_users = [{"id": i, "name": f"user_{i}"} for i in range(100)]

        projects_response = MockResponse(json_data=valid_projects, status_code=200)
        users_response = MockResponse(json_data=valid_users, status_code=200)
        mock_get.side_effect = [projects_response, users_response]

        fivetran_request = FivetranRequest(
            json={"secrets": {"access_token": "valid_key"}, "state": state}
        )
        response = main(fivetran_request)
        assert True is response["state"]["fetch_more_users"]
        assert True is response["state"]["fetch_more_projects"]
        assert True is response["hasMore"]
        assert 100 == response["state"]["users_offset"]
        assert 100 == response["state"]["projects_offset"]
        assert valid_projects["data"] == response["insert"]["projects"]
        assert valid_users == response["insert"]["users"]

    @mock.patch("casa.main.requests.get")
    def test_should_get_more_users_but_not_projects_previous_state(self, mock_get):
        state = {
            "users_offset": QUERY_RESULT_LIMIT,
            "projects_offset": QUERY_RESULT_LIMIT,
            "fetch_more_users": True,
            "fetch_more_projects": True,
        }
        valid_projects = {
            "data": [
                {"id": i, "name": f"project_{i}"}
                for i in range(90)  # Less than 100, shouldn't get more afterwards
            ]
        }
        valid_users = [{"id": i, "name": f"user_{i}"} for i in range(100)]

        projects_response = MockResponse(json_data=valid_projects, status_code=200)
        users_response = MockResponse(json_data=valid_users, status_code=200)
        mock_get.side_effect = [projects_response, users_response]

        fivetran_request = FivetranRequest(
            json={"secrets": {"access_token": "valid_key"}, "state": state}
        )

        response = main(fivetran_request)

        assert True is response["state"]["fetch_more_users"]
        assert False is response["state"]["fetch_more_projects"]
        assert True is response["hasMore"]
        assert 200 == response["state"]["users_offset"]
        assert 0 == response["state"]["projects_offset"]
        assert valid_projects["data"] == response["insert"]["projects"]
        assert valid_users == response["insert"]["users"]

    @mock.patch("casa.main.requests.get")
    def test_dont_fetch_projects_if_dont_need_to(self, mock_get):
        state = {
            "users_offset": QUERY_RESULT_LIMIT,
            "projects_offset": 0,
            "fetch_more_users": True,
            "fetch_more_projects": False,
        }
        valid_users = [{"id": i, "name": f"user_{i}"} for i in range(100)]

        mock_get.return_value = MockResponse(json_data=valid_users, status_code=200)

        fivetran_request = FivetranRequest(
            json={"secrets": {"access_token": "valid_key"}, "state": state}
        )
        response = main(fivetran_request)

        assert True is response["state"]["fetch_more_users"]
        assert False is response["state"]["fetch_more_projects"]
        assert True is response["hasMore"]
        assert 200 == response["state"]["users_offset"]
        assert 0 == response["state"]["projects_offset"]
        assert [] == response["insert"]["projects"]
        assert valid_users == response["insert"]["users"]

    @mock.patch("casa.main.requests.get")
    def test_reset_state_if_no_more_to_fetch(self, mock_get):
        state = {
            "users_offset": QUERY_RESULT_LIMIT,
            "projects_offset": QUERY_RESULT_LIMIT,
            "fetch_more_users": True,
            "fetch_more_projects": True,
        }
        valid_projects = {
            "data": [
                {"id": i, "name": f"project_{i}"}
                for i in range(90)  # Less than 100, shouldn't get more afterwards
            ]
        }
        valid_users = [
            {"id": i, "name": f"user_{i}"}
            for i in range(90)  # Less than 100, shouldn't get more afterwards
        ]
        projects_response = MockResponse(json_data=valid_projects, status_code=200)
        users_response = MockResponse(json_data=valid_users, status_code=200)
        mock_get.side_effect = [projects_response, users_response]

        fivetran_request = FivetranRequest(
            json={"secrets": {"access_token": "valid_key"}, "state": state}
        )
        response = main(fivetran_request)

        assert True is response["state"]["fetch_more_users"]
        assert True is response["state"]["fetch_more_projects"]
        assert False is response["hasMore"]
        assert 0 == response["state"]["users_offset"]
        assert 0 == response["state"]["projects_offset"]
        assert valid_projects["data"] == response["insert"]["projects"]
        assert valid_users == response["insert"]["users"]
