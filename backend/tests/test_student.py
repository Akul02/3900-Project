import pytest
from pytest_mock import MockerFixture
from uuid import uuid4
from flask.testing import FlaskClient
from datetime import datetime, timedelta, timezone
from prisma.models import Appointment, User
from pytest_mock.plugin import MockType


############################ GET PROFILE TESTS #################################


def test_get_args(
    setup_test: FlaskClient, find_unique_users_mock: MockType, fake_student: User
):
    client = setup_test

    # Missing id
    # resp = client.get("/student/")
    # assert resp.json == {"error": "id field was missing"}
    # assert resp.status_code == 405

    # Invalid id
    resp = client.get("/student/1")
    assert resp.json == {"error": "Profile does not exist"}
    assert resp.status_code == 404

    fake_student.location = "Australia"
    fake_student.name = "Name1"

    # Valid id
    resp = client.get(f"/student/{fake_student.id}")
    assert resp.status_code == 200
    assert resp.json["id"] == fake_student.id
    assert resp.json["name"] == "Name1"
    assert resp.json["profilePicture"] is None
    assert resp.json["location"] == "Australia"
    assert resp.json["phoneNumber"] is None


########################### MODIFY PROFILE TESTS ###############################


def test_modify_not_json(setup_test: FlaskClient):
    client = setup_test
    resp = client.put("/student/profile")
    assert resp.json == {"error": "content-type was not json or data was malformed"}
    assert resp.status_code == 415


# Non-admin modifying their profile
def test_modify_args(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_student: User,
):
    client = setup_test

    # No user logged in
    resp = client.put("/student/profile", json={})
    assert resp.json == {"error": "No user is logged in"}
    assert resp.status_code == 401

    resp = client.post(
        "/login",
        json={
            "email": "validemail@mail.com",
            "password": "12345678",
            "accountType": "student",
        },
    )

    find_unique_users_mock.assert_called_with(
        where={"email": fake_student.email}, include=mocker.ANY
    )

    # Invalid name
    resp = client.put("/student/profile", json={"name": ""})
    assert resp.json == {"error": "name field must be at least 1 character(s)"}
    assert resp.status_code == 400

    # Invalid email
    resp = client.put("/student/profile", json={"name": "Jerry", "email": ""})
    assert resp.json == {"error": "email field is invalid"}
    assert resp.status_code == 400

    # Invalid email 2
    resp = client.put("/student/profile", json={"name": "Jerry", "email": "hi"})
    assert resp.json == {"error": "email field is invalid"}
    assert resp.status_code == 400

    # Invalid email 3
    resp = client.put("/student/profile", json={"name": "Jerry", "email": "hello@hi"})
    assert resp.json == {"error": "email field is invalid"}
    assert resp.status_code == 400

    update_mock = mocker.patch("tests.conftest.UserActions.update")

    # Valid modification
    resp = client.put(
        "/student/profile",
        json={
            "name": "Name1",
            "email": "hello@hi.com",
            "bio": "",
            "profilePicture": "",
            "location": "Australia",
            "phoneNumber": "",
        },
    )
    update_mock.assert_called()

    assert resp.json == {"success": True}
    assert resp.status_code == 200


# Admin modifying a student profile
def test_admin_modify_args(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_student: User,
    fake_admin: User,
):
    client = setup_test

    resp = client.post(
        "/login",
        json={
            "email": "validemail@mail.com",
            "password": "12345678",
            "accountType": "student",
        },
    )
    find_unique_users_mock.assert_called_with(
        where={"email": fake_student.email}, include=mocker.ANY
    )

    resp = client.put("/student/profile", json={"id": fake_student.id})
    assert resp.json == {"error": "id field should not be supplied by a non admin user"}
    assert resp.status_code == 403

    resp = client.post("/logout")

    resp = client.post(
        "/login",
        json={
            "email": "validemail3@mail.com",
            "password": "12345678",
            "accountType": "admin",
        },
    )
    find_unique_users_mock.assert_called_with(
        where={"email": fake_admin.email}, include=mocker.ANY
    )

    # Missing id
    resp = client.put("/student/profile", json={})
    assert resp.json == {"error": "id field was missing"}
    assert resp.status_code == 400

    # Invalid name
    resp = client.put("/student/profile", json={"id": fake_student.id, "name": ""})
    assert resp.json == {"error": "name field must be at least 1 character(s)"}
    assert resp.status_code == 400

    # Invalid email
    resp = client.put(
        "/student/profile", json={"id": fake_student.id, "name": "Hi", "email": ""}
    )
    assert resp.json == {"error": "email field is invalid"}
    assert resp.status_code == 400

    # Invalid email 2
    resp = client.put(
        "/student/profile",
        json={"id": fake_student.id, "name": "Hi", "email": "hi"},
    )
    assert resp.json == {"error": "email field is invalid"}
    assert resp.status_code == 400

    # Invalid email 3
    resp = client.put(
        "/student/profile",
        json={"id": fake_student.id, "name": "Hi", "email": "hello@hi"},
    )
    assert resp.json == {"error": "email field is invalid"}
    assert resp.status_code == 400

    # Invalid id
    resp = client.put(
        "/student/profile",
        json={
            "id": "invalid",
            "name": "Name1",
            "bio": "",
            "email": "hello@hi.com",
            "profilePicture": "",
            "location": "Australia",
            "phoneNumber": "",
        },
    )
    find_unique_users_mock.assert_called_with(
        where={"id": "invalid"}, include=mocker.ANY
    )

    assert resp.json == {"error": "Profile does not exist"}
    assert resp.status_code == 404

    update_mock = mocker.patch("tests.conftest.UserActions.update")

    # Valid modification
    resp = client.put(
        "/student/profile",
        json={
            "id": fake_student.id,
            "name": "Name123",
            "bio": "hi",
            "email": "hello@hi.com",
            "profilePicture": "hi",
            "location": "Sydney",
            "phoneNumber": "000",
        },
    )
    update_mock.assert_called()

    assert resp.json == {"success": True}
    assert resp.status_code == 200

    fake_student.name = "Name123"
    fake_student.bio = "hi"
    fake_student.location = "Sydney"
    fake_student.phoneNumber = "000"

    resp = client.get(f"/student/{fake_student.id}")
    find_unique_users_mock.assert_called_with(
        where={"id": fake_student.id}, include=mocker.ANY
    )

    assert resp.status_code == 200
    assert resp.json["id"] == fake_student.id
    assert resp.json["name"] == "Name123"
    assert resp.json["bio"] == "hi"
    assert resp.json["location"] == "Sydney"
    assert resp.json["phoneNumber"] == "000"


########################### DELETE PROFILE TESTS ###############################


# No JSON
def test_delete_not_json(setup_test: FlaskClient):
    client = setup_test
    resp = client.delete("/student/")
    assert resp.json == {"error": "content-type was not json or data was malformed"}
    assert resp.status_code == 415


# No user logged in
def test_delete_no_user(setup_test: FlaskClient):
    client = setup_test
    resp = client.delete("/student/", json={})
    assert resp.json == {"error": "No user is logged in"}
    assert resp.status_code == 401


def test_delete_student_login(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_student: User,
):
    client = setup_test

    resp = client.post(
        "/login",
        json={
            "email": "validemail@mail.com",
            "password": "12345678",
            "accountType": "student",
        },
    )

    find_unique_users_mock.assert_called_with(
        where={"email": fake_student.email}, include=mocker.ANY
    )

    # Invalid id
    resp = client.delete("/student/", json={"id": "invalid"})
    assert resp.json == {"error": "id field should not be supplied by a non admin user"}
    assert resp.status_code == 403

    # Valid id
    resp = client.delete("/student/", json={"id": fake_student.id})
    assert resp.json == {"error": "id field should not be supplied by a non admin user"}
    assert resp.status_code == 403

    # No id
    resp = client.delete("/student/", json={})
    assert resp.json == {"success": True}
    assert resp.status_code == 200


def test_delete_admin_login(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_student: User,
    fake_admin: User,
):
    client = setup_test

    resp = client.post(
        "/login",
        json={
            "email": "validemail3@mail.com",
            "password": "12345678",
            "accountType": "admin",
        },
    )

    find_unique_users_mock.assert_called_with(
        where={"email": fake_admin.email}, include=mocker.ANY
    )

    # No id
    resp = client.delete("/student/", json={})
    assert resp.json == {"error": "id field was missing"}
    assert resp.status_code == 400

    # Invalid id
    resp = client.delete("/student/", json={"id": "invalid"})
    assert resp.json == {"error": "Profile does not exist"}
    assert resp.status_code == 404

    delete_mock = mocker.patch("tests.conftest.UserActions.delete")

    # Valid id
    resp = client.delete("/student/", json={"id": fake_student.id})
    delete_mock.assert_called()

    assert resp.json == {"success": True}
    assert resp.status_code == 200


########################### STUDENT APPOINTMENT TESTS ##########################


@pytest.fixture
def fake_appointments(fake_tutor, fake_student):
    apt1 = Appointment(
        id=str(uuid4()),
        startTime=datetime.now(timezone.utc) + timedelta(days=1, hours=0),
        endTime=datetime.now(timezone.utc) + timedelta(days=1, hours=1),
        tutorAccepted=False,
        tutor=fake_tutor.tutorInfo,
        tutorId=fake_tutor.id,
        student=fake_student.studentInfo,
        studentId=fake_student.id,
    )

    apt2 = Appointment(
        id=str(uuid4()),
        startTime=datetime.now(timezone.utc) + timedelta(days=1, hours=0),
        endTime=datetime.now(timezone.utc) + timedelta(days=1, hours=1),
        tutorAccepted=True,
        tutor=fake_tutor.tutorInfo,
        tutorId=fake_tutor.id,
        student=fake_student.studentInfo,
        studentId=fake_student.id,
    )

    apt3 = Appointment(
        id=str(uuid4()),
        startTime=datetime.now(timezone.utc) - timedelta(days=1, hours=1),
        endTime=datetime.now(timezone.utc) - timedelta(days=1),
        tutorAccepted=True,
        tutor=fake_tutor.tutorInfo,
        tutorId=fake_tutor.id,
        student=fake_student.studentInfo,
        studentId=fake_student.id,
    )
    fake_student.studentInfo.appointments = [apt1, apt2, apt3]

    return fake_student, apt1.id, apt2.id, apt3.id


def test_student_appointment_not_login(setup_test: FlaskClient):
    client = setup_test
    resp = client.get("/student/appointments")
    assert resp.json["error"] == "No user is logged in"
    assert resp.status_code == 401


def test_student_appointment_not_student_login(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_tutor: User,
):
    client = setup_test

    resp = client.post(
        "/login",
        json={
            "email": "validemail2@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )
    find_unique_users_mock.assert_called_with(
        where={"email": fake_tutor.email}, include=mocker.ANY
    )

    resp = client.get("/student/appointments")
    assert resp.json["error"] == "Current user is not a student"
    assert resp.status_code == 400


def test_student_appointments(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_appointments,
):
    client = setup_test

    data = fake_appointments

    resp = client.post(
        "/login",
        json={
            "email": "validemail@mail.com",
            "password": "12345678",
            "accountType": "student",
        },
    )
    find_unique_users_mock.assert_called_with(
        where={"email": data[0].email}, include=mocker.ANY
    )

    resp = client.get("student/appointments")
    resp.status_code == 200

    _, id1, id2, id3 = fake_appointments
    assert "requested" in resp.json
    assert "accepted" in resp.json
    assert "completed" in resp.json

    assert id1 in resp.json["requested"]
    assert id2 in resp.json["accepted"]
    assert id3 in resp.json["completed"]
