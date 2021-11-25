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

### Updating the CircleCI Config

To Update the CircleCI `config.yml` and add new connectors to the CI workflow run:

```
./fivetran ci_config update
```

### Setting up a Custom Connector in Fivetran

Before adding a new connector to Fivetran, create a new dataset via [bigquery-etl](https://github.com/mozilla/bigquery-etl)
where the connector will write data to. Datasets should be suffixed with `_export`.

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

Generally, data imports should be scheduled via [telemetry-airflow](https://github.com/mozilla/telemetry-airflow)
instead of Fivetrans built-in scheduling. Create a new DAG in telemetry-airflow, specify a `FivetranOperator` which
will trigger the Fivetran connector. `FivetranSensor` can be used to monitor the progress of the data import.
An example of what a data import DAG could look like can be found here: https://github.com/mozilla/telemetry-airflow/blob/main/dags/bugzilla.py

## Custom Connectors Development Notes

This is a collection of things to keep in mind/useful information when writing code for custom connectors.

### Passing Data into Connectors

To pass configuration data, such as API keys, into a custom connector a JSON object can be specified in the
Fivetran settings. The JSON object can be set as the "Secret". The connector can access the JSON data via 
the `request` object:

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
        // other data
    },
    "insert": {
        "table_name": [
            {"id":1, "value": 100},
            // rows that will get added to "table_name" table in BigQuery
        ],
        // ...
    },
    "delete": {},
    "schema" : {
        "table_name": {
            "primary_key": ["id"]
        },
        // ....
    },
    "hasMore" : true // or false
}
```

### Incremental Data Updates

To keep track of what data has already been imported in previous runs, Fivetran passes a `since_id` value
as part of the `state` object. `since_id` needs to be updated by the connector and can be set, for example,
to the date of the last data entry imported.

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

Google Cloud Functions have a couple of limitations. For instance, the maximum runtime is around 10 minutes and
available memory is limited. In some cases importing all data in one run might not be possible.

`hasMore` can be used to indicate to Fivetran to trigger the connector again to import more available data.
To keep track of what data has already been imported in previous runs, `state` has an `offset` value. `offset`
can, for example, be set to the date of the last data record imported.

`hasMore` and `offset` need to be updated every time the connector is triggered.

```python
def main(request):
    # [...]
    offset = 1
    if "offset" in request.json["state"]:
        offset = request.json["state"]["offset"]

    # fetch more data

    # [...]

    # udpate offset and hasMore
    return {
        "state": {
            "offset": offset + 1
        },
        "hasMore": has_more_data(data),
        # [...]
    }
```


### Other Resources

* https://github.com/fivetran/functions
* https://cloud.google.com/architecture/partners/building-custom-data-integrations-using-fivetran-and-cloud-functions
* https://fivetran.com/blog/serverless-etl-with-cloud-functions
