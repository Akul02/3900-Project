from flask import Blueprint, request, jsonify, session
from prisma.models import User, Student, Tutor, Appointment, Rating
from uuid import uuid4
from datetime import datetime
from helpers.views import student_view, tutor_view
from helpers.error_handlers import (
    ExpectedError,
    error_decorator,
)

appointment = Blueprint("appointment", __name__)


@appointment.route("request", methods=["POST"])
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

    try:
        st = datetime.fromisoformat(args["startTime"])
        et = datetime.fromisoformat(args["endTime"])
    except ValueError:
        raise ExpectedError("timeRange field(s) were malformed", 400)

    if not st < et:
        raise ExpectedError("endTime cannot be less than startTime", 400)
    elif st.replace(tzinfo=None) < datetime.now():
        raise ExpectedError("startTime must be in the future", 400)

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

    apt = (
        [appointment]
        if student.appointments == None
        else student.appointments + [appointment]
    )

    Student.prisma().update(
        where={"id": session["user_id"]},
        data={"appointments": {"connect": {"id": appointment.id}}},
    )

    return (
        jsonify(
            {
                "id": appointment.id,
                "startTime": appointment.startTime,
                "endTime": appointment.endTime,
                "studentId": appointment.studentId,
                "tutorId": appointment.tutorId,
                "tutorAccepted": appointment.tutorAccepted,
            }
        ),
        200,
    )


@appointment.route("rating", methods=["POST"])
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

    if not 1 <= args["rating"] <= 5:
        raise ExpectedError("Rating must be between 1 and 5", 400)

    if appointment.endTime > datetime.now():
        raise ExpectedError("Appointment isn't complete yet", 400)

    if session["user_id"] != appointment.studentId:
        raise ExpectedError("User is not the student of the appointment", 403)

    rating = Rating.prisma().create(
        data={
            "id": str(uuid4()),
            "score": args["rating"],
            "appointment": {"connect": {"id": args["id"]}},
            "appointmentId": args["id"],
            "createdFor": {"connect": {"id": appointment.tutorId}},
            "tutorId": appointment.tutorId,
        }
    )

    User.prisma().update(
        where={"id": rating["tutorId"]},
        data={"appointments": tutor_view(id=rating["tutorId"]).ratings + [rating]},
    )

    return jsonify({"success": True})
