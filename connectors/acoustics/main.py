import json
from typing import Any, Dict
import xmltodict
import requests


def main(request):
    """
    Function to execute.

    The standard format of `request` is a JSON object with the following fields:
        `agent`: informal object
        `state`: contains bookmark that marks the data Fivetran has already synced
        `secret`: optional JSON object that contains access keys or API keys
    """
    # acoustics authentication steps 1. Get auth token 2. Submit XML API call
    config = json.loads(request)["secrets"]
    # config = request.json['secrets']
    headers = {
                "content-type": "application/x-www-form-urlencoded"
             }
    data = {
            "grant_type": config["grant_type"],
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "refresh_token": config["refresh_token"]
            }
    token_response = requests.post(config["base_url"]+"/oauth/token",headers = headers,data = data )
    auth_token = json.loads(token_response.text)["access_token"]
    print(auth_token)

    # Step2 : POST get_aggregate_metric_for_org API call
    with open("./requests/get_agg_metric_org.json", "r") as agg:
        input = agg.read()
        dict_body = json.loads(input)

    body = xmltodict.unparse(dict_body)

    headers = {
        "content-type": "text/xml;charset=utf-8",
        "authorization": "Bearer "+auth_token
    }

    rsp = requests.post(config["base_url"]+"/XMLAPI",headers = headers,data = body )
    parsed_xml = xmltodict.parse(rsp.text)
    parsed_response = json.loads(json.dumps(parsed_xml))
    top_domains = parsed_response['Envelope']['Body']['RESULT']['TopDomains']
    print(top_domains)

    since_id = None
    tdLineItem = []
    for td in top_domains:
        #Add all required data points from the api response
        tdLineItem.append({
            "mailingId":td['TopDomain']['MailingId'],
            "reportId":td["ReportId"],
            "domain":td["Domain"],
            "sent":td["Sent"],
            "bounce": td["Bounce"],
            "open": td["Open"],
            "click": td["Click"],
            "unsubscribe": td["Unsubscribe"],
            "conversion":td["Conversion"]
        })

    # Send JSON response back to Fivetran
    state = {"since_id": {}}

    schema ={
        "mailing_line_item": {"primary_key": ["mailingId", "mailingId","domain"]}
    }

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

if __name__ == "__main__":
    # to be set and read via Fivetran UI, this is for testing only
    request = """{ "secrets":
        {
        "base_url": "https://api-campaign-us-6.goacoustic.com",
        "grant_type": "refresh_token",
        "client_id": "******",
        "client_secret": "*******",
        "refresh_token": "*********"
    }
    }"""
    main(request)