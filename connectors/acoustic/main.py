"""
Fivetran custom connector to pull email campaign report data from Acoustic
"""

from datetime import datetime, timedelta
from json import dumps
from typing import Any, List
import tempfile

import attr
import shutil
import requests
from acoustic.acoustic_client import DATE_FORMAT, AcousticClient, _get_size_in_mbs
from acoustic.model.agg_metric_org import AggMetricOrg
from acoustic.model.fivetran_response import FivetranResponse
from acoustic.model.moco_contact import MocoContact
from acoustic.model.reporting_raw_recipient_data_export import (
    ReportingRawRecipientDataRecord,
)


def extract_agg_metric_org_data(
    acoustic_client: AcousticClient, date_start: str, date_end: str
) -> List[Any]:
    request_template_file = "get_agg_metric_org.xml.jinja"

    request_params = {
        "private": False,
        "sent": False,
        "top_domain": False,
        "date_start": date_start,
        "date_end": date_end,
    }

    data = acoustic_client.get_agg_metric_org(
        request_template=f"{acoustic_client.REQUEST_TEMPLATE_PATH}/{request_template_file}",
        template_params=request_params,
    )

    print("INFO: Number of rows retrieved for agg_metrics_org: %s" % len(data))

    return data


def generate_report_raw_recipient_reporting_data(
    acoustic_client: AcousticClient, date_start: str, date_end: str
) -> List[Any]:
    request_template_file = "reporting_raw_recipient_data_export.xml.jinja"

    request_params = {
        "export_format": 0,
        "date_start": date_start,
        "date_end": date_end,
    }

    sftp_report_file = acoustic_client.generate_report(request_template=f"{acoustic_client.REQUEST_TEMPLATE_PATH}/{request_template_file}", template_params=request_params, report_type="raw_recipient_export")
    print(f"INFO: raw_recipient_export report has been generated and is available in the SFTP server: {sftp_report_file}")

    return sftp_report_file


def generate_contact_report(
    acoustic_client: AcousticClient, date_start: str, date_end: str
) -> List[Any]:
    request_template_file = "export_database.xml.jinja"

    request_params = {
        # "list_name": "Main Contact Table revision 3",
        "list_id": 1364939,
        "export_type": "ALL",
        "export_format": "CSV",
        "visibility": 1,  # 0 (Private) or 1 (Shared)
        "date_start": date_start,
        "date_end": date_end,
    }

    sftp_report_file = acoustic_client.generate_report(request_template=f"{acoustic_client.REQUEST_TEMPLATE_PATH}/{request_template_file}", template_params=request_params, report_type="contact_export")
    print(f"INFO: contact_export report has been generated and is available in the SFTP server: {sftp_report_file}")

    return sftp_report_file


def main(request: requests.Request) -> dict:
    """
    Function that will be executed by Fivetran.

    The standard format of `request` is a JSON object with the following fields:
        `agent`: informal object
        `state`: contains bookmark that marks the data Fivetran has already synced
        `secrets`: optional JSON object that contains access keys or API keys, other config

    Returns FivetranResponse as a dictionary.
    """

    # Seems like Fivetran is using PST time zone? (UTC - 8) important for Airflow scheduling Airflow should run at 8am UTC?
    # TODO: what is acoustic time setting?
    run_start_system_time = datetime.now()  # type: datetime

    # Configuration
    config = request.json["secrets"]  # type: ignore
    state = request.json["state"]  # type: ignore
    has_more_connectors = state.get("has_more", {"raw_recipient_export": False, "contact_export": False,})
    has_more_run = state.get("has_more_run", False)

    default_start_date = config["default_start_date"]  # type: str
    state_start_date = state.get("next_date_start")  # type: str
    start_date = state_start_date or default_start_date  # type: str
    date_start = datetime.strptime(start_date, DATE_FORMAT)  # type: datetime

    date_delta = timedelta(days=1)
    date_end = date_start + date_delta  # type: datetime

    # Ensuring that enough time elapsed to pull recent data
    # Otherwise return and wait for next run
    if (run_start_system_time - date_start) < date_delta:
        print(
            "WARNING: Skipping run as the difference between current_system_date (%s) \
             - date_start(%s) is less than date_delta (%s)"
            % (run_start_system_time, date_start, date_delta)
        )
        return attr.asdict(
            FivetranResponse(
                state={
                    "next_date_start": date_start.strftime(DATE_FORMAT),
                },
            )
        )

    print(
        "INFO: Starting Acoustic data export for date range: %s - %s | state: %s"
        % (date_start.strftime(DATE_FORMAT), date_end.strftime(DATE_FORMAT), state)
    )

    acoustic_client = AcousticClient(**config)

    # only generate report files on the first run of a day
    # and grab agg_metric_org data
    # initial_run = date_start.hour == 0 and date_start.minute == 0  # TODO: this won't work
    initial_run = has_more_run == False

    if initial_run:
        print("INFO: Starting inital run, generating reports...")

        raw_recipient_sftp_report_file = generate_report_raw_recipient_reporting_data(
            acoustic_client,
            date_start=date_start.strftime(DATE_FORMAT),
            date_end=date_end.strftime(DATE_FORMAT)
        )

        contact_sftp_report_file = generate_contact_report(
            acoustic_client,
            date_start=date_start.strftime(DATE_FORMAT),
            date_end=date_end.strftime(DATE_FORMAT)
        )

        agg_metric_org_data = extract_agg_metric_org_data(
            acoustic_client,
            date_start=date_start.strftime(DATE_FORMAT),
            date_end=date_end.strftime(DATE_FORMAT),
        )

        has_more = True

        state = {
            "next_date_start": date_start.strftime(DATE_FORMAT),
            'next_index': {'raw_recipient_export': 0, 'contact_export': 0},
            "has_more": {
                "contact_export": has_more,
                "raw_recipient_export": has_more,
            },
            "has_more_run": has_more,
            "sftp_files": {
                "raw_recipient_sftp_report_file": raw_recipient_sftp_report_file,
                "contacts_sftp_report_file": contact_sftp_report_file,
            }
        }

        response = attr.asdict(
            FivetranResponse(
                state=state,
                insert={
                    "agg_metric_org": agg_metric_org_data,
                    "reporting_raw_recipient_data_export": list(),
                    "contact_export": list(),
                },
                schema={
                    "agg_metric_org": AggMetricOrg.get_fivetran_schema(),
                    "reporting_raw_recipient_data_export": ReportingRawRecipientDataRecord.get_fivetran_schema(),
                    "contact_export": MocoContact.get_fivetran_schema(),
                },
                hasMore=has_more,
            )
        )

        print(state)

        print(
            "INFO: Completed Acoustic report generation: date range: %s - %s | "
            "next_date_start: %s | hasMore: %s | time taken: %s | "
            "Estimated response size: %s (in MBs)"
            % (
                date_start.strftime(DATE_FORMAT),
                date_end.strftime(DATE_FORMAT),
                state["next_date_start"],
                has_more,
                str(datetime.now() - run_start_system_time),
                str(_get_size_in_mbs(dumps(response))),
            )
        )

        return response  # need to return immediately within report generation step due to timeout during the initial run

    print("INFO: Retrieving data from report files...")

    raw_recipient_sftp_report_file = state.get("sftp_files", dict()).get("raw_recipient_sftp_report_file")
    contact_sftp_report_file = state.get("sftp_files", dict()).get("contacts_sftp_report_file")
    agg_metric_org_data = list()

    try:
        _tmp_dir = tempfile.mkdtemp(suffix=None, prefix=None, dir=None)

        raw_recipient_data = list()
        raw_recipient_next_index = state.get("next_index", dict()).get("raw_recipient_export", 0)
        if has_more_connectors["raw_recipient_export"]:
            print("INFO Starting processing raw_recipient_export data")

            raw_recipient_mb_limit = 4.0

            start = datetime.now()
            raw_recipient_report = acoustic_client.download_file_from_sftp(sftp_file=raw_recipient_sftp_report_file, target_dir=_tmp_dir)
            print(f"INFO: Downloaded {raw_recipient_sftp_report_file} for processing. Time taken: {str(datetime.now() - start)}")

            start = datetime.now()
            raw_recipient_next_index, raw_recipient_data = acoustic_client.get_data_from_report_file(report_file=raw_recipient_report, from_row=raw_recipient_next_index, data_limit=raw_recipient_mb_limit)
            print(f"INFO: Report processing took {str(datetime.now() - start)}. Number of rows for raw_recipient_data retrieved: {len(raw_recipient_data)}")


        contact_next_index = state.get("next_index", dict()).get("contact_export", 0)
        contact_data = list()
        if has_more_connectors["contact_export"]:
            print("INFO: Starting processing contact_export data...")

            contact_mb_limit = 4.0

            start = datetime.now()
            contact_report = acoustic_client.download_file_from_sftp(sftp_file=contact_sftp_report_file, target_dir=_tmp_dir)
            print(f"INFO: Downloaded {contact_report} for processing. Time taken: {str(datetime.now() - start)}")

            start = datetime.now()
            contact_next_index, contact_data = acoustic_client.get_data_from_report_file(report_file=contact_report, from_row=contact_next_index, data_limit=contact_mb_limit)
            print(f"INFO: Report processing took {str(datetime.now() - start)}. Number of rows for contact_data retrieved: {len(contact_data)}")

    finally:
        shutil.rmtree(_tmp_dir)

    inserts = {
        "agg_metric_org": agg_metric_org_data,
        "reporting_raw_recipient_data_export": raw_recipient_data,
        "contact_export": contact_data,
    }

    has_more = any([bool(raw_recipient_next_index), bool(contact_next_index)])  # TODO: this might not work anymore, maybe should check the length of the list?
    state = {
        "next_date_start": date_end.strftime(DATE_FORMAT) if not has_more else date_start.strftime(DATE_FORMAT),
        "next_index": {
            "raw_recipient_export": raw_recipient_next_index,
            "contact_export": contact_next_index,
        },
        "has_more": {
            "raw_recipient_export": bool(raw_recipient_next_index),
            "contact_export": bool(contact_next_index),
        },
        "has_more_run": has_more,
        "sftp_files": {
            "raw_recipient_sftp_report_file": raw_recipient_sftp_report_file if has_more else None,
            "contacts_sftp_report_file": contact_sftp_report_file if has_more else None,
        }
    }

    schema = {
        "agg_metric_org": AggMetricOrg.get_fivetran_schema(),
        "reporting_raw_recipient_data_export": ReportingRawRecipientDataRecord.get_fivetran_schema(),
        "contact_export": MocoContact.get_fivetran_schema(),
    }

    print(state)

    # TODO: if has_more is false should we delete the report files from the sftp server?

    response = attr.asdict(
        FivetranResponse(state=state, schema=schema, insert=inserts, hasMore=has_more)
    )

    print(
        "INFO: Completed Acoustic data export: date range: %s - %s | "
        "next_date_start: %s | hasMore: %s | time taken: %s | "
        "Estimated response size: %s (in MBs)"
        % (
            date_start.strftime(DATE_FORMAT),
            date_end.strftime(DATE_FORMAT),
            state["next_date_start"],
            has_more,
            str(datetime.now() - run_start_system_time),
            str(_get_size_in_mbs(dumps(response))),
        )
    )

    return response


if __name__ == "__main__":
    from os import getenv

    """
    In the active shell set env variables by executing:
    export CLIENT_ID=client_id
    export CLIENT_SECRET=client_secret
    export REFRESH_TOKEN=refresh_token
    export BASE_URL="https://api-campaign-us-6.goacoustic.com"
    export SFTP_HOST="transfer-campaign-us-6.goacoustic.com"
    """
    env_vars_to_load = (
        "CLIENT_ID",
        "CLIENT_SECRET",
        "REFRESH_TOKEN",
        "BASE_URL",
    )
    mock_secrets = {var.lower(): getenv(var) for var in env_vars_to_load}
    mock_secrets["default_start_date"] = "01/20/2021 00:00:00"

    mock_state = {
        "next_date_start": "01/20/2022 00:00:00",
        # "next_date_start": "01/20/2022 11:30:00",  # 10 minute delta fails - seems response is too large
        # "next_date_start": "02/10/2022 00:00:00",  # agg_metrics returns a list object with dict entries
        # "next_date_start": "01/20/2022 00:00:00",  # agg_metrics returns a single dict object with an entry
    }

    # dummy_request = requests.Request(
    #     "GET",
    #     "https://www.dummy.com/api/call",
    #     json={"state": mock_state, "secrets": mock_secrets},
    # )
    # result = main(dummy_request)

    # print(result)

    state = {'next_date_start': '01/20/2022 00:00:00', 'next_index': {'raw_recipient_export': 9348, 'contact_export': 1634}, 'has_more': True, 'sftp_files': {'raw_recipient_sftp_report_file': 'Raw Recipient Data Export Mar 03 2022 15-42-08 PM 1883.zip', 'contacts_sftp_report_file': '/download/Main Contact Table revision 3 - All - Mar 3 2022 07-42-20 AM.CSV'}}
    state = {'next_date_start': '01/20/2022 00:00:00', 'next_index': {'raw_recipient_export': 116312, 'contact_export': 20412}, 'has_more': True, 'sftp_files': {'raw_recipient_sftp_report_file': 'Raw Recipient Data Export Mar 03 2022 18-29-25 PM 1126.zip', 'contacts_sftp_report_file': '/download/Main Contact Table revision 3 - All - Mar 3 2022 10-29-45 AM.CSV'}}
    state = {
        'has_more': {
            "contact_export": False,
            "raw_recipient_export": True,
        },
        'next_date_start': '01/20/2022 00:00:00', 'next_index': {'contact_export': 20412, 'raw_recipient_export': 116312}, 'sftp_files': {'contacts_sftp_report_file': '/download/Main Contact Table revision 3 - All - Mar 3 2022 10-29-45 AM.CSV', 'raw_recipient_sftp_report_file': 'Raw Recipient Data Export Mar 03 2022 18-29-25 PM 1126.zip'}}

    # initial state - report generation
    state = {'next_date_start': '01/21/2022 00:00:00', 'next_index': {'raw_recipient_export': 0, 'contact_export': 0}, 'has_more': {'raw_recipient_export': False, 'contact_export': False}, 'has_more_run': False, 'sftp_files': {'raw_recipient_sftp_report_file': None, 'contacts_sftp_report_file': None}}
    # second state - data retrieval
    state = {'next_date_start': '01/21/2022 00:00:00', 'has_more': {'contact_export': True, 'raw_recipient_export': True}, 'has_more_run': True, 'sftp_files': {'raw_recipient_sftp_report_file': 'Raw Recipient Data Export Mar 04 2022 12-51-06 PM 954.zip', 'contacts_sftp_report_file': '/download/Main Contact Table revision 3 - All - Mar 4 2022 04-51-27 AM.CSV'}}
    # third run
    state = {'next_date_start': '01/21/2022 00:00:00', 'next_index': {'raw_recipient_export': 9401, 'contact_export': 1701}, 'has_more': {'raw_recipient_export': True, 'contact_export': True}, 'has_more_run': True, 'sftp_files': {'raw_recipient_sftp_report_file': 'Raw Recipient Data Export Mar 04 2022 12-51-06 PM 954.zip', 'contacts_sftp_report_file': '/download/Main Contact Table revision 3 - All - Mar 4 2022 04-51-27 AM.CSV'}}
    # raw_recipient_export index outside of range
    state = {'next_date_start': '01/21/2022 00:00:00', 'next_index': {'raw_recipient_export': 190002, 'contact_export': 3402}, 'has_more': {'raw_recipient_export': True, 'contact_export': True}, 'has_more_run': True, 'sftp_files': {'raw_recipient_sftp_report_file': 'Raw Recipient Data Export Mar 04 2022 12-51-06 PM 954.zip', 'contacts_sftp_report_file': '/download/Main Contact Table revision 3 - All - Mar 4 2022 04-51-27 AM.CSV'}}
    # raw_recipient_export and contact_export index outside of range
    state = {'next_date_start': '01/21/2022 00:00:00', 'next_index': {'raw_recipient_export': 190002, 'contact_export': 123402}, 'has_more': {'raw_recipient_export': True, 'contact_export': True}, 'has_more_run': True, 'sftp_files': {'raw_recipient_sftp_report_file': 'Raw Recipient Data Export Mar 04 2022 12-51-06 PM 954.zip', 'contacts_sftp_report_file': '/download/Main Contact Table revision 3 - All - Mar 4 2022 04-51-27 AM.CSV'}}
    # next day run, should re-generate report
    state = {'next_date_start': '02/22/2022 00:00:00', 'next_index': {'raw_recipient_export': 0, 'contact_export': 0}, 'has_more': {'raw_recipient_export': False, 'contact_export': False}, 'has_more_run': False, 'sftp_files': {'raw_recipient_sftp_report_file': 'Raw Recipient Data Export Mar 04 2022 12-51-06 PM 954.zip', 'contacts_sftp_report_file': '/download/Main Contact Table revision 3 - All - Mar 4 2022 04-51-27 AM.CSV'}}
    # ^^ did start report generation, but appears to be taking long time

    dummy_request_2 = requests.Request(
        "GET",
        "https://www.dummy.com/api/call",
        json={"state": state, "secrets": mock_secrets},
    )
    result_2 = main(dummy_request_2)

    # print(result_2)
