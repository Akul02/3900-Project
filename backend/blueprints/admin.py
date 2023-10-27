import re
from hashlib import sha256
from uuid import uuid4
from flask import Blueprint, jsonify, session
from prisma.models import User, Tutor, Admin, Student
from jsonschemas.user_search_schema import user_search_schema
from jsonschemas.admin_create_schema import admin_create_schema
from helpers.views import user_view, admin_view
from helpers.error_handlers import (
    validate_decorator,
    ExpectedError,
    error_decorator,
)

admin = Blueprint("admin", __name__)


@admin.route("/search", methods=["GET"])
@error_decorator
@validate_decorator("query_string", user_search_schema)
def user_search(args):
    if "user_id" not in session:
        raise ExpectedError("No user is logged in", 401)

    admin = admin_view(id=session["user_id"])
    if not admin:
        raise ExpectedError("Insufficient permission to search for users", 403)

    if "accountType" in args:
        match args["accountType"]:
            case "student":
                res = Student.prisma().find_many(include={"userInfo": True})
            case "tutor":
                res = Tutor.prisma().find_many(include={"userInfo": True})
            case "admin":
                res = Admin.prisma().find_many(include={"userInfo": True})

        users = map(lambda user: user.userInfo, res)
    else:
        users = User.prisma().find_many()

    if len(args) == 0:
        return jsonify({"userIds": [user.id for user in users]}), 200
    elif "id" in args:
        user = user_view(id=args["id"])
        if user:
            return jsonify({"userIds": [user.id]})

    valid_users = []
    for user in users:
        valid = True
        if "name" in args:
            valid &= re.search(args["name"].lower().strip(), user.name.lower()) != None

        if "phoneNumber" in args and user.phoneNumber:
            valid &= args["phoneNumber"] == user.phoneNumber
        elif "phoneNumber" in args:
            continue

        if "email" in args:
            valid &= args["email"] == user.email

        if valid:
            valid_users.append(user.id)

    return jsonify({"userIds": valid_users}), 200


@admin.route("/create", methods=["POST"])
@error_decorator
@validate_decorator("json", admin_create_schema)
def admin_create(args):
    if "user_id" not in session:
        raise ExpectedError("No user is logged in", 401)

    admin = admin_view(id=session["user_id"])
    if not admin:
        raise ExpectedError(
            "Insufficient permission to create a new admin account", 403
        )

    new_admin_id = str(uuid4())
    User.prisma().create(
        data={
            "id": new_admin_id,
            "name": args["name"],
            "email": args["email"],
            "hashedPassword": sha256(str(args["password"]).encode()).hexdigest(),
            "adminInfo": {"create": {"id": new_admin_id}},
        }
    )

    return jsonify({"id": new_admin_id}), 200
