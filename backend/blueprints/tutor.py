from flask import Blueprint, request, jsonify, session
from prisma.models import Tutor, Subject, User
from jsonschemas.tutor_modify_schema import tutor_modify_schema
from helpers.process_time_block import process_time_block
from helpers.views import tutor_view
from helpers.admin_id_check import admin_id_check
from helpers.rating_calc import rating_calc
from helpers.error_handlers import (
    validate_decorator,
    ExpectedError,
    error_decorator,
)

tutor = Blueprint("tutor", __name__)


@tutor.route("/<tutor_id>", methods=["GET"])
@error_decorator
def get_profile(tutor_id):
    tutor = tutor_view(id=tutor_id)
    if tutor is None:
        raise ExpectedError("Profile does not exist", 404)

    if tutor.course_offerings is None:
        course_offerings = []
    else:
        course_offerings = list(map(lambda c: c.name, tutor.course_offerings))

    if tutor.times_available is None:
        times_available = []
    else:
        times_available = list(
            map(
                lambda d: {
                    "startTime": d.startTime.isoformat(),
                    "endTime": d.endTime.isoformat(),
                },
                tutor.times_available,
            )
        )

    if tutor.ratings is None:
        rating = 0
    else:
        rating = rating_calc(tutor.ratings)

    return jsonify(
        {
            "id": tutor.id,
            "name": tutor.name,
            "bio": tutor.bio if tutor.bio else "",
            "email": tutor.email,
            "rating": rating,
            "profilePicture": tutor.profile_picture,
            "location": tutor.location,
            "phoneNumber": tutor.phone_number,
            "courseOfferings": course_offerings,
            "timesAvailable": times_available,
        }
    )


@tutor.route("/profile", methods=["PUT"])
@error_decorator
@validate_decorator("json", tutor_modify_schema)
def modify_profile(args):
    if "user_id" not in session:
        raise ExpectedError("No user is logged in", 400)

    modify_tutor_id = admin_id_check(args)

    tutor = tutor_view(id=modify_tutor_id)
    if tutor is None:
        raise ExpectedError("Profile does not exist", 404)

    name = tutor.name if "name" not in args else args["name"]
    bio = tutor.bio if "bio" not in args else args["bio"]
    email = tutor.email if "email" not in args else args["email"]

    profile_picture = (
        tutor.profile_picture
        if "profilePicture" not in args
        else args["profilePicture"]
    )
    location = tutor.location if "location" not in args else args["location"]
    phone_number = (
        tutor.phone_number if "phoneNumber" not in args else args["phoneNumber"]
    )
    if "courseOfferings" in args:
        addingSubjects(args["courseOfferings"], modify_tutor_id)

    if "timesAvailable" in args:
        addingTimes(args["timesAvailable"], modify_tutor_id)

    User.prisma().update(
        where={"id": tutor.id},
        data={
            "name": name,
            "bio": bio,
            "email": email,
            "profilePicture": profile_picture,
            "location": location,
            "phoneNumber": phone_number,
        },
    )

    return jsonify({"success": True})


@tutor.route("/", methods=["DELETE"])
@error_decorator
def delete_profile():
    args = request.get_json()

    if "user_id" not in session:
        raise ExpectedError("No user is logged in", 400)

    delete_tutor_id = admin_id_check(args)

    tutor = tutor_view(id=delete_tutor_id)
    if tutor is None:
        raise ExpectedError("Profile does not exist", 404)

    # All fields other than course_offerings will cascade delete in the db
    if tutor.course_offerings is not None:
        for subject in map(lambda c: c.name, tutor.course_offerings):
            Tutor.prisma().update(
                where={"id": tutor.id},
                data={"courseOfferings": {"disconnect": {"name": subject}}},
            )

    User.prisma().delete(where={"id": tutor.id})

    return jsonify({"success": True})


def addingSubjects(course_offerings, tutor_id):
    tutor = tutor_view(id=tutor_id)
    # tutor is adding/deleting subjects
    # wipe previous stuff, if there is any
    if tutor.course_offerings is not None:
        for subject in tutor.course_offerings:
            Tutor.prisma().update(
                where={"id": tutor_id},
                data={"courseOfferings": {"disconnect": {"name": subject.name}}},
            )

    # tutor is changing their subjects offered to zero
    if course_offerings is None or len(course_offerings) == 0:
        return

    # connect all subjects in the courseofferings list back to the tutor record
    # connect the tutor to the respective subject
    for subject_name in course_offerings:
        subject = Subject.prisma().find_first(where={"name": subject_name})

        if subject is None:
            Subject.prisma().create(data={"name": subject_name})

        Tutor.prisma().update(
            where={"id": tutor_id},
            data={"courseOfferings": {"connect": {"name": subject_name}}},
        )


def addingTimes(times_available, tutor_id):
    if times_available is None or len(times_available) == 0:
        Tutor.prisma().update(
            where={"id": tutor_id}, data={"timesAvailable": {"deleteMany": {}}}
        )
        return

    formatted_availabilities = sorted(
        map(lambda t: process_time_block(t), times_available),
        key=lambda d: d["startTime"],
    )

    to_create = []
    prev_block = None
    # create all the tutoravailability records again with the new timesAvailable
    for i, time_block in enumerate(formatted_availabilities):
        if i == 0:
            to_create.append(time_block)
            prev_block = time_block
            continue

        if prev_block["endTime"] > time_block["startTime"]:
            raise ExpectedError("Time availabilities should not overlap", 400)

        to_create.append(time_block)
        prev_block = time_block

    Tutor.prisma().update(
        where={"id": tutor_id}, data={"timesAvailable": {"deleteMany": {}}}
    )

    Tutor.prisma().update(
        where={"id": tutor_id},
        data={"timesAvailable": {"create": to_create}},
    )
