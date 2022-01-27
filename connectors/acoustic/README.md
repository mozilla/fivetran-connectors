# Acoustic Fivetran Connector

Acoustic Fivetran connector for retrieving Acoustic data. The API is only used to trigger a job in Acoustic to generate a "report" with the requested data, that is a compressed zip file containing one or more csv files.

This connector syncs the following data from Acoustic:
- [Raw contact events](https://developer.goacoustic.com/acoustic-campaign/reference/rawrecipientdataexport)
- [Contacts](https://developer.goacoustic.com/acoustic-campaign/reference/export-from-a-database)
- [Organization aggregate tracking metrics](https://developer.goacoustic.com/acoustic-campaign/reference/getaggregatetrackingfororg)


## Configuration

Authentication docs: https://developer.goacoustic.com/acoustic-campaign/reference/getting-started-with-oauth

The following configuration needs to be provided for the connector as a secret in Fivetran:

```json
{
    "base_url": "https://api-campaign-us-6.goacoustic.com",  // URL for a specific instance to use
    "sftp_host": "transfer-campaign-us-6.goacoustic.com",  // host where generated report will be available
    "client_id": "*********",
    "client_secret": "**********",
    "refresh_token": "**********",
    "default_start_date": "2020-01-01T00:00:00Z",
}
```

For manually testing the function from within the google.console UI, please use the following JSON format:
```json
{
    "secrets": {
        "client_id": "*********",
        "client_secret": "*********",
        "refresh_token": "*********",
        "base_url": "https://api-campaign-us-6.goacoustic.com",
        "sftp_host": "transfer-campaign-us-6.goacoustic.com",
        "default_start_date": "01/20/2022 00:00:00"
    },
    "state": {
        "next_date_start": "01/26/2022 00:00:00"
    }
}
```


## Configuration description

### Secret configuration
- `secret/base_url`: base url to be used for communicating with Acoustic API (https://developer.goacoustic.com/acoustic-campaign/reference/xml-api-overview-1#xml-api-endpoints)
- `secret/sftp_host`: host where generated report will be available for download
- `secret/client_id`: client identity
- `secret/client_secret`: secret that it uses to confirm its identity to the API
- `secret/refresh_token`: A long-lived value that the client store, the refresh_token establishes the relationship between a specific client and a specific user
- `secret/default_start_date` - date from when to run a backfill (only used on first run), after initial run next_date_start should be set and used (this happens automatically)

### State configuration
- `state/next_date_start` - set at the end of the run to be equivalent to current value of `next_date_start` + `delta interval` (currently: 15 mins)
used to facilitate backfills rather than continue data retrieval for the same date. This is because of how the API works.
- `state/hasMore`/`has_more` - used to keep a sync running until data for the original `next_date_start` is pulled. `has_more` is set to `False` when date_end calculated is no longer on the same day as `date_start`.


## Deploying the connector to Cloud Function (dev)
Run the following command from root directory:
```
make deploy CONNECTOR_NAME=acoustic TIMEOUT=500
```


## Notes
- Acoustic Campaign archives emails automatically after 450 days by default (450 is max and this number can only be reduced) (_source: [Acoustic Campaign XML APIS Reporting](https://developer.goacoustic.com/acoustic-campaign/reference/reporting)_).
- Up to 10 concurrent requests are allowed to our API servers at any given time when using the OAuth method for authentication
