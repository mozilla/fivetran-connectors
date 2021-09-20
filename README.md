# fivetran-connectors

Custom connectors for [Fivetran](https://fivetran.com/) implemented as Google Cloud Functions.

## Development

The tools in this repository are intended for Python 3.8+.

To install dependencies:

```
pip install -r requirements.txt
```

### Creating a New Connector

To add a new connector run:

```
./tools/generate <name_of_connector>
```

`<name_of_connector>` is the name of the new connector for which a new directory will be created
in the `connectors/` directory. The new connector directory will be automatically populated with
boilerplate code.

### Updating the CircleCI Config

To Update the CircleCI `config.yml` and add new connectors to the CI workflow run:

```
./tools/ci_config
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

## Custom Connectors

[todo] Add more documentation

Some helpful resources when writing custom connectors:
* https://github.com/fivetran/functions
* https://cloud.google.com/architecture/partners/building-custom-data-integrations-using-fivetran-and-cloud-functions
