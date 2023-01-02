# fivetran-connectors

Custom connectors for [Fivetran](https://fivetran.com/) implemented as Google Cloud Functions.

## Development

The tools in this repository are intended for Python 3.8+.

To install the CLI:

```
./fivetran bootstrap
```

### Creating a New Connector

To add a new connector run:

```
./fivetran connector create <name_of_connector>
```

`<name_of_connector>` is the name of the new connector for which a new directory will be created
in the `connectors/` directory. The new connector directory will be automatically populated with
boilerplate code.

### Deploying Connectors

To deploy a connector as a Google Cloud Function, the connector needs to be added to the `deploy.yaml` file:

```yaml
<connector-name>:     # name of the new Google Cloud Function (must be unique)
  connector: <connector-type>   # name of the connector as specified in connectors/
  environment: dev         # determines the GCP project the connector is deployed to
```

The connector will be deployed after the CircleCI configuration has been updated and pushed to `main`.

During development connectors can also be deployed quickly via:

```
cd connectors/new_connector
gcloud functions deploy new_connector --entry-point main --runtime python38 --trigger-http --timeout=540 --memory=4096MB
```
This does not require the code to be merged into `main`.

### Updating the CircleCI Config

To Update the CircleCI `config.yml` and add new connectors to the CI workflow run:

```
./fivetran ci_config update
```

## Custom Connector Development

This is a collection of things to keep in mind/useful information when writing code for custom connectors.

By default the `main()` method in the `main.py` file for the connector will be they entry point for the Cloud Function.

### Passing Data into Connectors

To pass configuration data, such as API keys, into a custom connector a JSON object can be specified in the Fivetran settings. The JSON object can be set as the "Secret". The connector can access the JSON data via the `request` object:

```python
def main(request):
    config = request.json['secrets']
```

### Connector Response Format

The expected response format for connectors is: 

```json
{
    "state": {
        "since_id": "2018-01-02T00:00:01Z",
        /* other data */
    },
    "insert": {
        "table_name": [
            {"id":1, "value": 100},
            /* rows that will get added to "table_name" table in BigQuery */
        ],
        /* ... */
    },
    "delete": {},
    "schema" : {
        "table_name": {
            "primary_key": ["id"]
        },
        /* .... */
    },
    "has_more" : true /* if there is more data available that can be imported; or false */
}
```
More about the response format can be found [here](https://fivetran.com/docs/functions/google-cloud-functions#responseformat)

### Incremental Data Updates

To keep track of what data has already been imported in previous runs, Fivetran passes a `since_id` value as part of the `state` object. `since_id` needs to be updated by the connector and can be set, for example, to the date of the last data entry imported.

```python
def main(request):
    # [...]

    since_id = request.json["state"]["since_id"]

    # make API request to get data added after since_id
    data = api.get_data(last_modified=since_id)

    # [...]
    # update since_id
    return {
        "state": {
            "since_id": max_date(data)
            # [...]
        },
        # [...]
    }
```

### Follow-up Calls to Fetch more Data

Google Cloud Functions have a couple of limitations. For instance, the maximum runtime is around 10 minutes and available memory is limited. In some cases importing all data in one run might not be possible.

`has_more` can be used to indicate to Fivetran to trigger the connector again to import more available data. To keep track of what data has already been imported in previous runs, `state` has an `offset` value. `offset` can, for example, be set to the date of the last data record imported.

`has_more` and `offset` need to be updated every time the connector is triggered.

```python
def main(request):
    # [...]
    offset = 1
    if "offset" in request.json["state"]:
        offset = request.json["state"]["offset"]

    # fetch more data

    # [...]

    # udpate offset and has_more
    return {
        "state": {
            "offset": offset + 1
        },
        "has_more": has_more_data(data),
        # [...]
    }
```

## Connector Deployment

Once a new connector has been added and committed to `main` CircleCI will automatically deploy it
as a Google Cloud Function to the `dev-fivetran` project.

When setting up a new custom connector in Fivetran for the first time, copy the trigger URL of the
deployed function:

![Cloud Function Trigger URL](https://github.com/mozilla/fivetran-connectors/blob/main/docs/gcloud-function.png)

In Fivetran, add a new "Google Cloud Function" connector, set the "Destination schema" as the
create BigQuery destination dataset. Paste the trigger URL in the "Function Trigger" field.

The "Secrets" field is an optional JSON object that the Cloud Function connector will have access to.
This JSON object can, for example, contain API access keys or other configuration values. Once the
new connector has been configured, hit "Save and Test". The connector will get triggered to run an
initial data import.

Generally, data imports should be scheduled via [telemetry-airflow](https://github.com/mozilla/telemetry-airflow) instead of Fivetrans built-in scheduling. Since Fivetran usually dumps data into a destination that is not accessible, it is also necessary to set up some ETL to transform the data and write it to an accessible destination. Both the ETL and the scheduling can be specified in [bigquery-etl](https://github.com/mozilla/bigquery-etl).

When writing the query to create derived datasets in bigquery-etl add [the Fivetran import tasks to the scheduling config](https://github.com/mozilla/bigquery-etl/blob/b1a1f5a484ac8ab77c841d1c666bc02e3ccf9ee2/docs/reference/scheduling.md?plain=1#L57). Once changes are merged into main the DAG in Airflow will get updated automatically. Looking at the generated DAGs, each Fivetran task references a **Fivetran connector ID** that needs to be configured as an Airflow variable.

To configure this variable, in the **Airflow Admin - Variables** settings add a new entry. The **Key** needs to be set to the variable name as shown in the DAG source, the **Value** is the Fivetran connector ID which can be copied from the _Connection Details_ of the Fivetran connector _Setup_ tab.

Once configured, the Airflow DAG needs to be enabled.

## How to Debug Issues

1. Check Airflow errors to see which connector is affected.
    * The Airflow logs will not offer a lot of details on what went wrong. Instead they will link to the logs in Fivetran which are a little more helpful.
2. Check Fivetran logs of the connector.
    * Go to [Fivetran dashboard](https://fivetran.com/dashboard/connectors)
    * Check the connector logs. `reason` might provide some indication on what went wrong, whether it was a Fivetran specific issue or whether the connector encountered a problem.
3. Check the connector logs.
    * [Go to the deployed Google Cloud Function](https://console.cloud.google.com/functions/list?env=gen1&project=dev-fivetran) an check the logs for stack traces to determine what went wrong
5. Fix connector
    * If the connector needs to be fixed, deploy a new version (happens automatically when merged on `main`)
6. Reconnect connector in Fivetran
    * Connectors need to be manually reconnected in Fivetran
    * Navigate to the _Setup_ tab of the connector and click on _Test Connection_. Wait for the tests to finish.
test
