from jsonschemas.reused_properties import (
    name_prop,
    id_prop,
    phone_number_prop,
    email_prop,
    account_type_prop,
)

user_search_schema = {
    "$id": "/jsonschemas/user_search",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "user_search_schema",
    "type": "object",
    "properties": {
        **id_prop,
        **name_prop,
        **phone_number_prop,
        **email_prop,
        **account_type_prop,
    },
}
