from typing import Dict


# Makes a prop be able to accept their original type + null/None
# example usage:
# make_or_null(**email_prop, **password_prop) ->
# {'email': {'type': ['string', 'null'], 'format': 'email'}, 'password': {'type': ['string', 'null'], 'minLength': 8}}
def make_or_null(**kwargs) -> Dict[str, Dict]:
    # works with multiple properties of 'depth' 1
    for property in kwargs.values():
        if (
            "type" in property
            and isinstance(property["type"], str)
            and property["type"] != "null"
        ):
            property["type"] = [property["type"], "null"]

    return kwargs


email_prop = {
    "email": {
        "type": "string",
        "pattern": r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",
    },
}

password_prop = {
    "password": {
        "type": "string",
        "minLength": 8,
    },
}

account_type_prop = {
    "accountType": {
        "type": "string",
        "pattern": "student|tutor|admin",
    }
}

id_prop = {
    "id": {
        "type": "string",
    }
}

bio_prop = {
    "bio": {
        "type": "string",
    }
}

name_prop = {
    "name": {
        "type": "string",
        "minLength": 1,
    }
}

location_prop = {
    "location": {
        "type": "string",
    }
}

rating_prop = {
    "rating": {
        "type": "integer",
        "minimum": 1,
        "maximum": 5,
    }
}

profile_picture_prop = {
    "profilePicture": {
        "type": "string",
    }
}

phone_number_prop = {
    "phoneNumber": {
        "type": "string",
    }
}

course_offerings_prop = {
    "courseOfferings": {
        "type": "array",
        "items": {
            "type": "string",
        },
    }
}

times_available_prop = {
    "timesAvailable": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "startTime": {
                    "type": "string",
                },
                "endTime": {
                    "type": "string",
                },
            },
            "required": ["startTime", "endTime"],
        },
    }
}
