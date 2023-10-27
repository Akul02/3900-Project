from jsonschemas.reused_properties import location_prop, name_prop

tutor_search_schema = {
    "$id": "/jsonschemas/tutor_search",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "tutor_search_schema",
    "type": "object",
    "properties": {
        **name_prop,
        **location_prop,
        # rating is a string in this case
        "rating": {
            "type": "string",
            "pattern": "[1-5]",
        },
        # It's entered as a json dumped string
        "timeRange": {
            "type": "string",
        },
        # It's entered as a json dumped string
        "courseOfferings": {
            "type": "string",
        },
    },
}
