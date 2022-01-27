"""
Class describing the structure of Organization aggregate tracking metrics record/row
"""

import attr


@attr.s(auto_attribs=True)
class AggMetricOrg:
    """
    Represents a record/row of agg_metric_org (Organization aggregate tracking metrics)
    returned by Acoustic API.
    Acoustic docs:
    https://developer.goacoustic.com/acoustic-campaign/reference/getaggregatetrackingfororg
    """

    MailingId: int = attr.ib()
    ReportId: int = attr.ib()
    MailingName: str = attr.ib()
    NumAbuseFwd: int = attr.ib()
    NumAttachOpenFwd: int = attr.ib()
    NumBounceHard: int = attr.ib()
    NumBounceHardFwd: int = attr.ib()
    NumBounceSoft: int = attr.ib()
    NumBounceSoftFwd: int = attr.ib()
    NumChangeAddressFwd: int = attr.ib()
    NumClickFwd: int = attr.ib()
    NumConversionAmount: int = attr.ib()
    NumConversionAmountFwd: int = attr.ib()
    NumConversions: int = attr.ib()
    NumGrossAbuse: int = attr.ib()
    NumGrossAttach: int = attr.ib()
    NumGrossAttachOpenFwd: int = attr.ib()
    NumGrossChangeAddress: int = attr.ib()
    NumGrossClick: int = attr.ib()
    NumGrossClickFwd: int = attr.ib()
    NumGrossClickstreamFwd: int = attr.ib()
    NumGrossClickstreams: int = attr.ib()
    NumGrossConversionsFwd: int = attr.ib()
    NumGrossForwardFwd: int = attr.ib()
    NumGrossMailBlock: int = attr.ib()
    NumGrossMailRestriction: int = attr.ib()
    NumGrossMedia: int = attr.ib()
    NumGrossMediaFwd: int = attr.ib()
    NumGrossOpen: int = attr.ib()
    NumGrossOpenFwd: int = attr.ib()
    NumGrossOther: int = attr.ib()
    NumInboxMonitored: int = attr.ib()
    NumMailBlockFwd: int = attr.ib()
    NumMailRestrictionFwd: int = attr.ib()
    NumOtherFwd: int = attr.ib()
    NumSeeds: int = attr.ib()
    NumSent: int = attr.ib()
    NumSuppressed: int = attr.ib()
    NumSuppressedFwd: int = attr.ib()
    NumUniqueAttach: int = attr.ib()
    NumUniqueAttachOpenFwd: int = attr.ib()
    NumUniqueClick: int = attr.ib()
    NumUniqueClickFwd: int = attr.ib()
    NumUniqueClickstreamFwd: int = attr.ib()
    NumUniqueClickstreams: int = attr.ib()
    NumUniqueConversionsFwd: int = attr.ib()
    NumUniqueForwardFwd: int = attr.ib()
    NumUniqueMedia: int = attr.ib()
    NumUniqueMediaFwd: int = attr.ib()
    NumUniqueOpen: int = attr.ib()
    NumUniqueOpenFwd: int = attr.ib()
    NumUnsubscribes: int = attr.ib()
    SentDateTime: str = attr.ib()

    @staticmethod
    def get_fivetran_schema():
        return {
            "primary_key": [
                "MailingId",
                "ReportId",
            ],
        }
