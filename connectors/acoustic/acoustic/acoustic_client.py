"""
Module for authenticating into and interacting with Acoustic (XML) API

Acoustic API docs can be found here: https://developer.goacoustic.com/acoustic-campaign/reference/overview
"""

import csv
from datetime import datetime
import os
import shutil
import tempfile
import zipfile
from collections import OrderedDict
from time import sleep
from typing import List
from sys import getsizeof
from json import dumps


import attr
import jinja2
import paramiko
import requests
import xmltodict  # type: ignore
from acoustic.model.reporting_raw_recipient_data_export import (
    ReportingRawRecipientDataRecord,
)

DATE_FORMAT = "%m/%d/%Y %H:%M:%S"


def _request_wrapper(request_method, request_body):
    _response = request_method(**request_body)
    _response.raise_for_status()
    return _response

def _get_size_in_mbs(obj):
        # source: https://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python

        response_size_estimate_bytes = getsizeof(dumps(obj))

        return round(
            response_size_estimate_bytes / float(1 << 20), 2
        )


class AcousticClient:
    """
    Acoustic Client object for authenticating into and interacting with Acoustic XML API.
    """

    DEFAULT_BASE_URL = "https://api-campaign-us-6.goacoustic.com"
    XML_API_ENDPOINT = "XMLAPI"

    DEFAULT_SFTP_HOST = "transfer-campaign-us-6.goacoustic.com"
    SFTP_PORT = 22
    SFTP_USERNAME = "oauth"
    SFTP_FOLDER = "download"

    REQUEST_TEMPLATE_PATH = "request_templates"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        base_url: str = None,
        sftp_host: str = None,
        **kwargs,
    ):
        """
        :param client_id: to provide the client identity
        :param client_secret: secret that it used to confirm identity to the API
        :param refresh_token: A long-lived value that the client store,
        the refresh_token establishes the relationship between a specific client and a specific user.

        :return: Instance of AcousticClient class
        """

        self.base_url = base_url or AcousticClient.DEFAULT_BASE_URL
        self.sftp_host = sftp_host or AcousticClient.DEFAULT_SFTP_HOST
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._access_token = self._generate_access_token()

    def _generate_access_token(self) -> str:
        """
        Responsible for contacting Acoustic XML API and generating an access_token using Oauth method
        to be used for interacting with the API and retrieving data in the following calls.

        :return: A short-lived token that can be generated based on the refresh token.
            A value that is ultimately passed to the API to prove that this client is authorized
            to make API calls on the user’s behalf.

        More info about Acoustic and Oauth:
        https://developer.goacoustic.com/acoustic-campaign/reference/overview#getting-started-with-oauth
        """

        auth_endpoint = "oauth/token"
        url = f"{self.base_url}/{auth_endpoint}"

        _grant_type = "refresh_token"
        _request_body = {
            "grant_type": _grant_type,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "refresh_token": self._refresh_token,
        }

        headers = {
            "content-type": "application/x-www-form-urlencoded",
        }

        request = {
            "url": url,
            "headers": headers,
            "data": _request_body,
        }

        response = _request_wrapper(request_method=requests.post, request_body=request)

        return response.json()["access_token"]

    def get_agg_metric_org(
        self, request_template: str, template_params: dict
    ) -> List[dict]:
        """
        Extracts a listing of Acoustic Campaign emails that are sent for an organization
        for a specified date range and provides metrics for those emails.


        :param request_template: path to XML template file containing request body template to be used
        :param template_params: values that should be used to render the request template provided

        :return: Returns back a list of rows of data returned by the API call as a dictionary

        More information about the specific API call:
        https://developer.goacoustic.com/acoustic-campaign/reference/reporting#getaggregatetrackingfororg
        """

        with open(request_template, "r") as _file:
            request_body_template = jinja2.Template(_file.read())

        request_body = request_body_template.render(**template_params)

        request = {
            "url": f"{self.base_url}/{self.XML_API_ENDPOINT}",
            "headers": {
                "content-type": "text/xml;charset=utf-8",
                "authorization": f"Bearer {self._access_token}",
            },
            "data": request_body,
        }

        response = _request_wrapper(request_method=requests.post, request_body=request)

        data = xmltodict.parse(response.text)
        result_data = data["Envelope"]["Body"]["RESULT"]

        if not result_data["SUCCESS"].lower() == "true":
            """
            Example response when there is no mailing info found
            OrderedDict(
                [('Envelope', OrderedDict([('Body', OrderedDict(
                    [('RESULT', OrderedDict(
                        [('SUCCESS', 'false')])), ('Fault', OrderedDict(
                            [('Request', None), ('FaultCode', None), ('FaultString', 'No mailings.'), ('detail', OrderedDict(
                                [('error', OrderedDict([('errorid', '156'), ('module', None), ('class', 'SP.API'), ('method', None)]))])
                            )])
                        )])
                    )])
                )]
            )
            """  # noqa: E501
            if data["Envelope"]["Body"]["Fault"]["FaultCode"]:
                error_message = (
                    f"There has been a problem with retrieving data for the timeframe provided"
                    f"{template_params['date_start']}-{template_params['date_end']})."
                    "Error returned: {data['Envelope']['Body']['Fault']['FaultString']}"
                )
                raise RuntimeError(error_message)

            print(
                "WARNING: No results were found for agg_metric_org for the timeframe provided (%s - %s)"
                % (template_params["date_start"], template_params["date_end"])
            )
            return list(dict())

        mailing_data = result_data["Mailing"]

        # TODO: should we run the data through a data model before returning?
        if isinstance(mailing_data, list):
            return [dict(entry) for entry in result_data["Mailing"]]
        elif isinstance(mailing_data, OrderedDict):
            return [mailing_data]

        raise ValueError(
            "Unexpected data returned by Acoustic: data type: %s" % type(mailing_data)
        )

    def _is_job_complete(self, job_id: int, extra_info: str = None) -> bool:
        """
        Checks status of an Acoustic job to generate a report.

        :param job_id: Acoustic job id to check the progress status of

        :return: Returns True if job status in Acoustic is showing as complete
        """

        get_job_status_request_body_template = (
            f"{self.REQUEST_TEMPLATE_PATH}/get_job_status.xml.jinja"
        )

        with open(get_job_status_request_body_template, "r") as _file:
            request_body_template = jinja2.Template(_file.read())

        request_body = request_body_template.render(job_id=job_id)

        request = {
            "url": f"{self.base_url}/{self.XML_API_ENDPOINT}",
            "headers": {
                "content-type": "text/xml;charset=utf-8",
                "authorization": f"Bearer {self._access_token}",
            },
            "data": request_body,
        }

        response = _request_wrapper(request_method=requests.post, request_body=request)

        data = xmltodict.parse(response.text)

        job_status = data["Envelope"]["Body"]["RESULT"]["JOB_STATUS"].lower()
        print(
            "INFO: Current status for Acoustic job_id: %s is %s (%s)"
            % (job_id, job_status, extra_info or "")
        )

        return "complete" == job_status

    def generate_report(
        self, request_template: str, template_params: dict, report_type: str,
    ) -> str:
        """
        Extracts a listing of Acoustic Campaign emails that are sent for an organization
        for a specified date range and provides metrics for those emails.


        :param request_template: path to XML template file containing request body template to be used
        :param template_params: values that should be used to render the request template provided

        :return: Returns back a list of rows of data returned by the API call as a dictionary

        More information about the specific API call:
        https://developer.goacoustic.com/acoustic-campaign/reference/reporting#getaggregatetrackingfororg
        """

        supported_report_types = ("raw_recipient_export", "contact_export",)
        if report_type not in supported_report_types:
            pass  # TODO: raise with options

        with open(request_template, "r") as _file:
            request_body_template = jinja2.Template(_file.read())

        request_body = request_body_template.render(**template_params)

        request = {
            "url": f"{self.base_url}/{self.XML_API_ENDPOINT}",
            "headers": {
                "content-type": "text/xml;charset=utf-8",
                "authorization": f"Bearer {self._access_token}",
            },
            "data": request_body,
        }

        start = datetime.now()
        sleep_delay = 20

        response = _request_wrapper(request_method=requests.post, request_body=request)
        data = xmltodict.parse(response.text)

        if report_type == "contact_export":
            job_id = data["Envelope"]["Body"]["RESULT"]["JOB_ID"]
            export_file = data["Envelope"]["Body"]["RESULT"]["FILE_PATH"]
        elif report_type == "raw_recipient_export":
            job_id, export_file = data["Envelope"]["Body"]["RESULT"]["MAILING"].values()

        while not self._is_job_complete(job_id=job_id, extra_info=report_type):
            sleep(sleep_delay)

        print(f"INFO: {report_type} generation complete. Time taken: {datetime.now() - start}")

        return export_file

    def download_file_from_sftp(self, sftp_file: str, target_dir: str):
        target_local_filename = sftp_file.lower().replace(" ", "_").lstrip("/").split("/")[-1]  # TODO: is this renaming really necessary?
        target_local_full_path = f"{target_dir}/{target_local_filename}"

        with paramiko.Transport((self.sftp_host, self.SFTP_PORT)) as _transport:
            _transport.connect(None, self.SFTP_USERNAME, self._access_token)

            with paramiko.SFTPClient.from_transport(_transport) as _sftp:  # type: ignore
                _sftp.get(f"/download/{sftp_file.lstrip('/download/')}", target_local_full_path)

        return target_local_full_path

    def get_data_from_report_file(self, report_file: str, from_row: int, data_limit: float = None) -> List[dict]:
        next_index = 0

        if report_file.split(".")[-1] == "zip":
            _tmp_dir = f"/{'/'.join(report_file.lstrip('/').split('/')[:-1])}"
            with zipfile.ZipFile(report_file, "r") as zip_ref:
                    zip_ref.extractall(_tmp_dir)

                    extracted_file = list(filter(lambda x: ".csv" in x, os.listdir(_tmp_dir)))[0]  # grabbing first item TODO: is it always just one file?
                    report_file = f"{_tmp_dir}/{extracted_file}"

        with open(report_file) as csv_file:
            entries = list(csv.DictReader(csv_file))
            num_of_entries = len(entries)

            chunk_size = 100
            until = from_row + chunk_size

            while _get_size_in_mbs(entries[from_row: until]) <= data_limit:
                until += chunk_size

                if until >= num_of_entries:
                    until = num_of_entries
                    break

                next_index = until + 1

        return next_index, entries[from_row: until]
