from flask import Blueprint, jsonify, session
from helpers.error_handlers import error_decorator
from helpers.views import student_view, tutor_view, admin_view

utils = Blueprint("utils", __name__)


@utils.route("/getuserid", methods=["GET"])
@error_decorator
def get_id():
    if "user_id" in session:
        student = student_view(id=session["user_id"])
        tutor = tutor_view(id=session["user_id"])
        admin = admin_view(id=session["user_id"])
        if student:
            account_type = "student"
        elif tutor:
            account_type = "tutor"
        elif admin:
            account_type = "admin"
        else:
            return jsonify({}), 401
        return jsonify({"id": session["user_id"], "accountType": account_type}), 200
    else:
        return jsonify({}), 401
