"""
Class describing the structure of raw recipient data record/row
"""

import attr


# TODO: maybe just use dataclass? Is the initial DWH stage enforcing schema?
#       What should we do here?
@attr.s(auto_attribs=True)
class ReportingRawRecipientDataRecord:
    """
    Represents a record/row of raw recipient data (Export raw contact events)
    returned by Acoustic API.
    Acoustic docs:
    https://developer.goacoustic.com/acoustic-campaign/reference/rawrecipientdataexport
    """

    recipient_id: str = attr.ib()
    recipient_type: str = attr.ib()
    mailing_id: str = attr.ib()
    report_id: str = attr.ib()
    campaign_id: str = attr.ib()
    email: str = attr.ib()
    event_type: str = attr.ib()
    event_timestamp: str = attr.ib()
    body_type: str = attr.ib()
    content_id: str = attr.ib()
    click_name: str = attr.ib()
    url: str = attr.ib()
    conversion_action: str = attr.ib()
    conversion_detail: str = attr.ib()
    conversion_amount: str = attr.ib()
    suppression_reason: str = attr.ib()
    customerid: str = attr.ib()
    address: str = attr.ib()

    # TODO: should we have additional validation for some of the fields?

    # def __attrs_post_init__(self):
    #     # todo: may need to n/a
    #     some_attr = "{0:.8f}".format(self.my_attr)
    #     self.my_attr = float(some_attr or 0.0)

    @staticmethod
    def get_fivetran_schema():
        return {
            "primary_key": [
                "Recipient Id",
                "Mailing Id",
                "Campaign Id",
            ],
        }
