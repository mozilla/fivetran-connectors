# Bugzilla Fivetran Connector

Fivetran connector for Bugzilla.

Currently the connector can fetch the following data:
* Products
* Components
* Bugs

## Configuration

The following configuration needs to be provided for the connector:

```json
{
    "url": "https://bugzilla.mozilla.org/rest/" // URL to Bugzilla instance,
    "api_key": "*********" // API key
    "max_date": "2014-09-01T19:12:17Z"  // max. date to backfill to (only used on first run)
    "bug_limit": "1000" // max. number of bugs fetched when connector gets invoked
}
```

If available data exceeds `bug_limit`, then `hasMore` will be set to `true` in the response.
This will result in Fivetran invoking the function again to fetch more bugs.
