"""
Fivetran response object model
"""

from typing import Any, Dict

import attr


@attr.s(auto_attribs=True)
class FivetranResponse:
    """
    Structure Fivetran expects main() to return. The response is a JSON object with five root nodes:

    - state: contains the updated state value(s).

    - insert: specifies the entities and records to be inserted.
        Fivetran reads the data and infers the data type and the number of columns.
    - delete: (optional) specifies the entities and records to be deleted. Use this node to mark records as deleted.
        Fivetran doesn't delete the record; instead it marks the record as deleted by setting
        _fivetran_deleted column value to true.
        If you specify the delete node, you must also specify the schema node.

    - schema: (optional) specifies primary key columns for each entity.
        you must be very consistent with the schema node and
        the primary key columns to avoid any unwanted behavior.
        If you don’t specify the schema, Fivetran appends the data.

    - hasMore: is an indicator for Fivetran to make a follow-up call for fetching the next set of data.
        Fivetran keeps making repeated calls until it receives hasMore = false.

    More details: https://fivetran.com/docs/functions#responseformat
    """

    state: Dict[str, Any] = attr.ib(validator=attr.validators.instance_of(dict))
    schema: Dict[Any, Any] = attr.ib(
        validator=attr.validators.instance_of(dict), default=dict()
    )
    insert: Dict[Any, Any] = attr.ib(
        validator=attr.validators.instance_of(dict), default=dict()
    )
    delete: Dict[Any, Any] = attr.ib(
        validator=attr.validators.instance_of(dict), default=dict()
    )
    hasMore: bool = attr.ib(validator=attr.validators.instance_of(bool), default=False)
