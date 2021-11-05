This connector reads `projects` and `users` from the CASA API in response to Fivetran requests. 

See the Biztera - CASA API documentation [here](https://biztera.com/developer/docs/api). Note that (at the time of this writing) the projects endpoint
is not detailed here.

This connector does a full import on every sync (mostly because the project and user endpoints don't offer easy date-based offsets). This should be fine because:
1. The data volume here is low (~hundreds to thousands of rows)
2. Fivetran charges for Monthly _Active_ Rows (emphasis mine). According to the [documentation](https://fivetran.com/docs/getting-started/consumption-based-pricing#determiningmar), 
updating(in this case syncing and only potentially updating) the same row (based on primary key - id) in this case multiple times in a months still counts as a single monthly active row.