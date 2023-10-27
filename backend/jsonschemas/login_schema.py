from jsonschemas.reused_properties import email_prop, password_prop, account_type_prop

login_schema = {
    "$id": "/jsonschemas/login",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "login_schema",
    "type": "object",
    "properties": {
        **email_prop,
        **password_prop,
        **account_type_prop,
    },
    "required": ["email", "password", "accountType"],
}
