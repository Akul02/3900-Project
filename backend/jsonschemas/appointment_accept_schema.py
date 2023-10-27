from jsonschemas.reused_properties import id_prop

appointment_accept_schema = {
    "$id": "/jsonschemas/appointment_accept",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "appointment_accept_schema",
    "type": "object",
    "properties": {
        **id_prop,
        "accept": {
            "type": "boolean",
        },
    },
    "required": ["id", "accept"],
}
