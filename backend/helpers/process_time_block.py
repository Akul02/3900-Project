from typing import TypedDict
from datetime import datetime, timezone
from uuid import uuid4
from helpers.error_handlers import ExpectedError


class ISOTimeBlock(TypedDict, total=True):
    # camelCase as passed key names are camelCase
    startTime: str
    endTime: str


# Typed return type isn't strictly needed, but helps with
# intellisense/autocomplete
class DTTimeBlock(TypedDict):
    # camelCase to match with TutorAvailability model in schema
    id: str
    # ! Note: These are UTC offset-aware datetimes
    startTime: datetime
    endTime: datetime


def process_time_block(time_block: ISOTimeBlock) -> DTTimeBlock:
    try:
        # standardise timezone by converting to utc
        st = datetime.fromisoformat(time_block["startTime"]).replace(
            tzinfo=timezone.utc
        )
        et = datetime.fromisoformat(time_block["endTime"]).replace(tzinfo=timezone.utc)
    except ValueError:
        raise ExpectedError("startTime and/or endTime field(s) was malformed", 400)

    if st > et:
        raise ExpectedError("endTime cannot be less than startTime", 400)

    return {"id": str(uuid4()), "startTime": st, "endTime": et}
