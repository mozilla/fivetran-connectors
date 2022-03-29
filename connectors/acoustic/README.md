# Acoustic Fivetran Connector (SFTP)

This integration consists of the following elements:
- __Acoustic__ - the source system that requires some configuration.
- __Airflow DAG__ - trigger and wait for report generation in Acoustic, once completed trigger Fivetran connector.
- __Fivetran SFTP connector__ (out of the box) - checks for file changes in the SFTP server and syncs those to BigQuery.

The Acoustic -> BigQuery integration syncs the following data from Acoustic:
- [Raw contact events](https://developer.goacoustic.com/acoustic-campaign/reference/rawrecipientdataexport) - information about mailing activity per user (send, open, click, etc.)
- [Contacts](https://developer.goacoustic.com/acoustic-campaign/reference/export-from-a-database) - information about users/contacts stored in Acoustic

## Acoustic configuration

1. [Set up an "Application" in Acoustic](https://help.goacoustic.com/hc/en-us/articles/360043157333-Application-account-access) (see: `Add applications` section)
1. [Retrieve client_id, client_secret, and refresh_token](https://help.dataq.ai/en/articles/2829268-where-do-i-find-my-acoustic-campaign-client-id-client-secret-or-refresh-token) (these will need to be added to Airflow as a connection) (NOTE: `refresh_token` will be sent to the admin user via email)
1. [Create a user for Fivetran to authenticate into the Acoustic SFTP server](https://help.goacoustic.com/hc/en-us/articles/360042640954-Add-or-update-users) (see: `Add or update users` section)
1. [Ensure the Fivetran Acoustic account has access to the application created in the first step](https://help.goacoustic.com/hc/en-us/articles/360043157333-Application-account-access) (see: `Add account access` section)


## Airflow configuration

1. Make sure Acoustic Airflow DAG contains configuration for the data type (for example: [contact_export](# TODO: add Github link once code is merged))
1. Ensure `acoustic` connection exists in the Airflow deployment (if not create it, see: `Airflow connection` below)
1. Make sure for each Acoustic data type defined in the DAG all required Airflow variables exist (for example: Fivetran connector id).


### Airflow connection

```
Conn Id: acoustic
Conn Type: HTTP
Description: Used to authenticate into Acoustic to generate data which then gets consumed by Fivetran
Host: https://api-campaign-us-6.goacoustic.com
Schema:
Login: CLIENT_ID
Password: CLIENT_SECRET
Port:
Extra: {"refresh_token": "dummy_refresh_token"}
```

### Airflow variables
Variables use the following naming convention:
`fivetran_acoustic_{data_type}_export_{variable_name}`

```
fivetran_acoustic_raw_recipient_export_connector_id: Fivetran connector ID to trigger

fivetran_acoustic_contact_export_connector_id: Fivetran connector ID to trigger
fivetran_acoustic_contact_export_list_id: List ID to export (contacts_dev: 1390189 | contacts_prod: 1364939)
```


## Fivetran configuration

### Setting up the connector (SFTP)

1. Navigate over to Fivetrain Dashboard and open the correct project.
2. Press `ADD CONNECTOR` (top right corner)
3. Search for `SFTP` connector type and select it and press `CONTINUE SETUP`.
4. Fill out the fields (please refer to the sections below for specific settings for each type of data)
5. For authentication you can use `Login with keypair` or username and password ([more info here](https://help.goacoustic.com/hc/en-us/articles/360042859494-SFTP)).
5. Press `SAVE & TEST`
6. Navigate to your new Fivetran connector and go the the `Setup` tab.
7. Copy the `Fivetran Connector ID` value and add it to `fivetran_acoustic` Airflow DAG. # TODO: add link here once merged

### Specific configuration: raw contact events (raw_recipient_report)
```
Host: campaign-us-6.goacoustic.com
Username: <acoustic_username>
Folder Path: /download/
Schema: acoustic_sftp
Table: raw_recipient_export
Pattern: Raw\sRecipient\sData[\w\s-]+\.zip
Archive Pattern:
File Reading Behavior:
Read all files as csv
Compression Behavior: Decompress all files with zip
Error Handling: Fails a file sync if improperly formatted data detected
Modified File Merge: Overwrite Rows
Escape Character:
Delimiter:
Null Sequence:
Headerless CSV?: false
```


### Specific configuration: contacts (Main Contact Table revision 3)

```
Host: campaign-us-6.goacoustic.com
Username: <acoustic_username>
Folder Path: /download/
Schema: acoustic_sftp
Table: contact_export
Pattern:
Master\sContact\sDatabase[\s\w-]+\.(csv|CSV)
Archive Pattern:
File Reading Behavior: Read all files as csv
Compression Behavior: No compression
Error Handling: Fails a file sync if improperly formatted data detected
Modified File Merge: Overwrite Rows
Escape Character:
Delimiter:
Null Sequence:
Headerless CSV?: false
```

---

__IMPORTANT__

_Please note that only once Airflow triggers a Fivetran run then the schedule of the connector changes to manually trigerred._

---

## Notes
- Acoustic Campaign archives emails automatically after 450 days by default (450 is max and this number can only be reduced) (_source: [Acoustic Campaign XML APIS Reporting](https://developer.goacoustic.com/acoustic-campaign/reference/reporting)_).
