from flask import Blueprint, request, jsonify, session
from prisma.errors import RecordNotFoundError
from prisma.models import User, Student, Tutor, Appointment, Rating
from jsonschemas.appointment_accept_schema import appointment_accept_schema
from helpers.process_time_block import process_time_block
from uuid import uuid4
from datetime import datetime
from helpers.views import student_view, tutor_view
from helpers.error_handlers import (
    validate_decorator,
    ExpectedError,
    error_decorator,
)

appointment = Blueprint("appointment", __name__)


@appointment.route("/accept", methods=["PUT"])
@error_decorator
@validate_decorator("json", appointment_accept_schema)
def appointment_accept(args):
    if "user_id" not in session:
        raise ExpectedError("No user is logged in", 401)

    tutor = tutor_view(id=session["user_id"])
    if not tutor:
        raise ExpectedError("Must be a tutor to modify appointments", 403)

    try:
        appointment = Appointment.prisma().update(
            where={"id": args["id"], "tutorId": tutor.id},
            data={"tutorAccepted": args["accept"]},
        )
    except RecordNotFoundError:
        raise ExpectedError(
            "Appointment corresponding to id does not exist or, appointment does not involve tutor",
            400,
        )

    return (
        jsonify(
            {
                "id": appointment.id,
                "startTime": appointment.startTime.isoformat(),
                "endTime": appointment.endTime.isoformat(),
                "studentId": appointment.studentId,
                "tutorId": appointment.tutorId,
                "tutorAccepted": appointment.tutorAccepted,
            }
        ),
        200,
    )


@appointment.route("/request", methods=["POST"])
@error_decorator
def a_request():
    args = request.get_json()

    if "user_id" not in session:
        raise ExpectedError("No user is logged in", 401)

    if "startTime" not in args or len(str(args["startTime"]).lower().strip()) == 0:
        raise ExpectedError("startTime field was missing", 400)

    if "endTime" not in args or len(str(args["endTime"]).lower().strip()) == 0:
        raise ExpectedError("endTime field was missing", 400)

    if "tutorId" not in args:
        raise ExpectedError("Tutor id field was missing", 400)

    data = process_time_block(
        {"startTime": args["startTime"], "endTime": args["endTime"]}
    )
    st = data["startTime"]
    et = data["endTime"]

    tutor = tutor_view(id=args["tutorId"])
    if not tutor:
        raise ExpectedError("Tutor profile does not exist", 400)

    student = student_view(id=session["user_id"])
    if not student:
        raise ExpectedError("Profile is not a student", 400)

    if student.appointments != None:
        for appointment in student.appointments:
            if (
                appointment.startTime <= st < appointment.endTime
                or appointment.startTime < et <= appointment.endTime
            ):
                raise ExpectedError(
                    "Appointment overlaps with another appointment", 400
                )

    appointment = Appointment.prisma().create(
        data={
            "id": str(uuid4()),
            "startTime": args["startTime"],
            "endTime": args["endTime"],
            "tutorAccepted": False,
            "tutor": {"connect": {"id": args["tutorId"]}},
            "student": {"connect": {"id": session["user_id"]}},
        }
    )

    # Student.prisma().update(
    #     where={"id": session["user_id"]},
    #     data={"appointments": {"connect": {"id": appointment.id}}},
    # )

    return (
        jsonify(
            {
                "id": appointment.id,
                "startTime": appointment.startTime.isoformat(),
                "endTime": appointment.endTime.isoformat(),
                "studentId": appointment.studentId,
                "tutorId": appointment.tutorId,
                "tutorAccepted": appointment.tutorAccepted,
            }
        ),
        200,
    )


@appointment.route("", methods=["DELETE"])
@error_decorator
def delete():
    args = request.get_json()

    if "user_id" not in session:
        raise ExpectedError("No user is logged in", 401)

    if "id" not in args or len(str(args["id"]).lower().strip()) == 0:
        raise ExpectedError("id field was missing", 400)

    tutor = tutor_view(id=session["user_id"])
    if not tutor:
        raise ExpectedError("Logged in user is not a tutor", 404)

    appointment = Appointment.prisma().find_unique(where={"id": args["id"]})
    if not appointment:
        raise ExpectedError("Appointment does not exist", 404)

    if tutor.appointments is None or appointment not in tutor.appointments:
        raise ExpectedError("Logged in user is not the tutor of the appointment", 403)

    Appointment.prisma().delete(where={"id": args["id"]})

    return jsonify({"success": True}), 200


@appointment.route("", methods=["PUT"])
@error_decorator
def modify():
    args = request.get_json()

    if "user_id" not in session:
        raise ExpectedError("No user is logged in", 401)

    if "id" not in args or len(str(args["id"]).lower().strip()) == 0:
        raise ExpectedError("id field was missing", 400)

    if "startTime" not in args or len(str(args["startTime"]).lower().strip()) == 0:
        raise ExpectedError("startTime field was missing", 400)

    if "endTime" not in args or len(str(args["endTime"]).lower().strip()) == 0:
        raise ExpectedError("endTime field was missing", 400)

    data = process_time_block(
        {"startTime": args["startTime"], "endTime": args["endTime"]}
    )
    st = data["startTime"]
    et = data["endTime"]

    tutor = tutor_view(id=session["user_id"])
    if not tutor:
        raise ExpectedError("Logged in user is not a tutor", 404)

    appointment = Appointment.prisma().find_unique(where={"id": args["id"]})
    if not appointment:
        raise ExpectedError("Appointment does not exist", 404)

    if appointment not in tutor.appointments:
        raise ExpectedError("Logged in user is not the tutor of the appointment", 403)

    for apt in tutor.appointments:
        if apt != appointment and (
            apt.startTime <= st < apt.endTime or apt.startTime < et <= apt.endTime
        ):
            raise ExpectedError("Appointment overlaps with another appointment", 400)

    Appointment.prisma().update(
        where={"id": args["id"]},
        data={"startTime": args["startTime"], "endTime": args["endTime"]},
    )

    return jsonify({"success": True}), 200


@appointment.route("/rating", methods=["POST"])
@error_decorator
def rating():
    args = request.get_json()

    if "user_id" not in session:
        raise ExpectedError("No user is logged in", 401)

    if "id" not in args or len(str(args["id"]).lower().strip()) == 0:
        raise ExpectedError("id field was missing", 400)

    if "rating" not in args or len(str(args["rating"]).lower().strip()) == 0:
        raise ExpectedError("rating field was missing", 400)

    appointment = Appointment.prisma().find_unique(where={"id": args["id"]})
    if not appointment:
        raise ExpectedError("Appointment does not exist", 400)

    if session["user_id"] != appointment.studentId:
        raise ExpectedError("User is not the student of the appointment", 403)

    if appointment.endTime.replace(tzinfo=None) > datetime.now():
        raise ExpectedError("Appointment isn't complete yet", 400)

    if not 1 <= args["rating"] <= 5:
        raise ExpectedError("Rating must be between 1 and 5", 400)

    rating = Rating.prisma().create(
        data={
            "id": str(uuid4()),
            "score": args["rating"],
            "appointment": {"connect": {"id": args["id"]}},
            "createdFor": {"connect": {"id": appointment.tutorId}},
        }
    )

    Tutor.prisma().update(
        where={"id": session["user_id"]},
        data={"ratings": {"connect": {"id": rating.id}}},
    )

    return jsonify({"success": True})
