from flask import Blueprint, request, jsonify, session
from prisma.models import Tutor, Student, Admin
from re import fullmatch
from uuid import uuid4
from hashlib import sha256
from helpers.error_handlers import (
    ExpectedError,
    error_decorator,
)

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["POST"])
@error_decorator
def register():
    args = request.get_json()

    if "name" not in args or len(str(args["name"]).lower().strip()) == 0:
        raise ExpectedError("name field was missing", 400)

    if "email" not in args or not fullmatch(
        r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",
        str(args["email"]).lower().strip(),
    ):
        raise ExpectedError("email field is invalid", 400)

    if "password" not in args or len(str(args["password"]).lower().strip()) < 8:
        raise ExpectedError("password field must be at least 8 characters long", 400)

    new_user_id = None
    if "accountType" in args:
        student = Student.prisma().find_first(where={"email": args["email"]})
        tutor = Tutor.prisma().find_first(where={"email": args["email"]})
        if student or tutor:
            raise ExpectedError("user already exists with this email", 400)

        match str(args["accountType"]).lower().strip():
            case "student":
                new_user_id = str(uuid4())
                Student.prisma().create(
                    data={
                        "id": new_user_id,
                        "name": args["name"],
                        "email": args["email"],
                        "hashedPassword": sha256(
                            str(args["password"]).encode()
                        ).hexdigest(),
                        "bio": "",
                        "appointments": {},
                    }
                )
            case "tutor":
                new_user_id = str(uuid4())
                Tutor.prisma().create(
                    data={
                        "id": new_user_id,
                        "name": args["name"],
                        "email": args["email"],
                        "hashedPassword": sha256(
                            str(args["password"]).encode()
                        ).hexdigest(),
                        "bio": "",
                        "rating": {},
                        "courseOfferings": {},
                        "timesAvailable": {},
                        "appointments": {},
                    }
                )
            case _:
                raise ExpectedError("accountType must be 'student' or 'tutor'", 400)
    else:
        raise ExpectedError("accountType field missing", 400)

    session["user_id"] = new_user_id

    return jsonify({"id": new_user_id}), 200
