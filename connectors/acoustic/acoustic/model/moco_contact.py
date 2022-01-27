"""
Class describing the structure of a Moco Contact record/row
"""

import attr


@attr.s(auto_attribs=True)
class MocoContact:
    """
    Represents a record/row of Moco Contact in Acoustic
    returned by Acoustic API.
    """

    # TODO: seems like there are some differences between schema
    # shown by Fivetran and BigQuery?

    email_id: str = attr.ib()
    sfdc_id: str = attr.ib()
    fxa_id: str = attr.ib()
    amo_add_on_ids: str = attr.ib()
    amo_display_name: str = attr.ib()
    amo_email_opt_in: int = attr.ib()
    amo_language: str = attr.ib()
    amo_last_login: str = attr.ib()
    amo_location: str = attr.ib()
    amo_profile_url: str = attr.ib()
    amo_user: int = attr.ib()
    amo_user_id: int = attr.ib()
    amo_username: str = attr.ib()
    basket_token: str = attr.ib()
    clickeddate: str = attr.ib()
    cohort: str = (
        attr.ib()
    )  # TODO: seems to be missing form BQ schema that was created?
    create_timestamp: str = attr.ib()
    double_opt_in: int = attr.ib()
    email: str = attr.ib()
    email_format: str = attr.ib()
    email_lang: str = attr.ib()
    emailtype: int = attr.ib()
    first_name: str = attr.ib()
    flag_for_contact_deletion: str = attr.ib()
    fxa_account_deleted: int = attr.ib()
    fxa_created_date: str = attr.ib()
    fxa_first_service: str = attr.ib()
    fxa_lang: str = attr.ib()
    fxa_login_date: str = attr.ib()
    fxa_primary_email: str = attr.ib()
    has_opted_out_of_email: int = attr.ib()
    last_name: str = attr.ib()
    mailing_country: str = attr.ib()
    mofo_segment: int = attr.ib()
    opendate: str = attr.ib()
    optedout: bool = attr.ib()
    optedoutdate: str = attr.ib()
    optindate: str = attr.ib()
    optindetails: str = attr.ib()
    optoutdetails: str = attr.ib()
    sub_miti: int = attr.ib()
    sub_mixed_reality: int = attr.ib()
    sub_mozilla_fellowship_awardee_alumni: int = attr.ib()
    sub_mozilla_festival: int = attr.ib()
    sub_mozilla_foundation: int = attr.ib()
    sub_mozilla_technology: int = attr.ib()
    sub_mozillians_nda: int = attr.ib()
    sub_rally: int = attr.ib()
    sub_take_action_for_the_internet: int = attr.ib()
    sub_test_pilot: int = attr.ib()
    sumo_contributor: int = attr.ib()
    sumo_user: int = attr.ib()
    sumo_username: int = attr.ib()
    unsubscribe_reason: str = attr.ib()
    vpn_waitlist_geo: str = attr.ib()
    vpn_waitlist_platform: str = attr.ib()
    zzz_confirm_firefox_news: int = attr.ib()
    zzz_confirm_hubs: int = attr.ib()
    zzz_confirm_miti: int = attr.ib()
    zzz_confirm_mozilla_fellowship_awardee_alumni: int = attr.ib()
    zzz_confirm_mozilla_festival: int = attr.ib()
    zzz_confirm_mozilla_foundation: int = attr.ib()
    zzz_confirm_mozilla_technology: int = attr.ib()
    zzz_confirm_test_pilot: int = attr.ib()
    zzz_welcome_apps_and_hacks: int = attr.ib()
    zzz_welcome_common_voice: int = attr.ib()
    zzz_welcome_firefox_news: int = attr.ib()
    zzz_welcome_knowledge_is_power: int = attr.ib()
    zzz_welcome_miti: int = attr.ib()
    zzz_welcome_mozilla_fellowship_awardee_alumni: int = attr.ib()
    zzz_welcome_mozilla_festival: int = attr.ib()
    zzz_welcome_mozilla_foundation: int = attr.ib()
    zzz_welcome_take_action_for_the_internet: int = attr.ib()
    zzz_welcome_test_pilot: int = attr.ib()
    zzz_welcome_about_mozilla: int = attr.ib()
    zzz_welcomeconfirm_common_voice: int = attr.ib()
    zzz_welcome_firefox_sweepstakes: int = attr.ib()

    @staticmethod
    def get_fivetran_schema():
        return {
            "primary_key": [
                "sfdc_id",
                "fxa_id",
                "email_id",
            ],
        }
