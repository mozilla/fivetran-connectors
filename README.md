# fivetran-connectors

Custom connectors for [Fivetran](https://fivetran.com/) implemented as Google Cloud Functions.

## Development

The tools in this repository are intended for python 3.8+.

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
