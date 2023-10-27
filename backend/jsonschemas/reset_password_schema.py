from jsonschemas.reused_properties import id_prop

reset_password_schema = {
    "$id": "/jsonschemas/reset_password_schema",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "reset_password_schema",
    "type": "object",
    "properties": {
        **id_prop,
        "newPassword": {
            "type": "string",
            "minLength": 8,
        },
    },
    "required": ["id", "newPassword"],
}
