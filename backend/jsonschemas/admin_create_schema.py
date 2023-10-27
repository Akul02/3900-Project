from jsonschemas.reused_properties import email_prop, password_prop, name_prop

admin_create_schema = {
    "$id": "/jsonschemas/admin_create",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "admin_create_schema",
    "type": "object",
    "properties": {
        **name_prop,
        **email_prop,
        **password_prop,
    },
    "required": ["name", "email", "password"],
}
