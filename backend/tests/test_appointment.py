from uuid import uuid4
import pytest
from datetime import datetime
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType
from flask.testing import FlaskClient
from prisma.models import Appointment, User, Rating
from prisma.errors import RecordNotFoundError

########################### APPOINTMENT ACCEPT TESTS ###########################


@pytest.fixture
def appointment_update_mock(mocker: MockerFixture, fake_tutor, fake_appointment):
    apt = fake_appointment

    def mocked_appointment_update(**kwargs):
        if (
            "tutorId" in kwargs["where"] and kwargs["where"]["tutorId"] == fake_tutor.id
        ) and ("id" in kwargs["where"] and kwargs["where"]["id"] == apt.id):
            apt.tutorAccepted = (
                kwargs["data"]["tutorAccepted"]
                if "data" in kwargs and "tutorAccepted" in kwargs["data"]
                else apt.tutorAccepted
            )
            return apt
        else:
            raise RecordNotFoundError(
                mocker.Mock(), message="from mocked appointment update"
            )

    return mocker.patch(
        "tests.conftest.AppointmentActions.update",
        new=mocker.Mock(side_effect=mocked_appointment_update),
    )


def test_appointment_accept_missing_args(setup_test: FlaskClient):
    client = setup_test

    # Id was missing from field
    resp = client.put("/appointment/accept", json={})
    assert resp.json["error"] == "'id' was missing from field(s)"
    assert resp.status_code == 400

    # accept was missing from field
    resp = client.put("/appointment/accept", json={"id": "id"})
    assert resp.json["error"] == "'accept' was missing from field(s)"
    assert resp.status_code == 400

    # Nothing missing, but not login
    resp = client.put("/appointment/accept", json={"id": "id", "accept": True})
    assert resp.json["error"] == "No user is logged in"
    assert resp.status_code == 401


def test_appointment_accept_student_login(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_student,
):
    client = setup_test

    # login as student
    client.post(
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

    resp = client.put("/appointment/accept", json={"id": "id", "accept": True})
    assert resp.json["error"] == "Must be a tutor to modify appointments"
    assert resp.status_code == 403


def test_appointment_accept_invalid_id(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    appointment_update_mock: MockType,
    fake_tutor,
):
    client = setup_test

    # login as tutor
    client.post(
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

    resp = client.put("/appointment/accept", json={"id": "id", "accept": True})
    appointment_update_mock.assert_called()

    assert (
        resp.json["error"]
        == "Appointment corresponding to id does not exist or, appointment does not involve tutor"
    )
    assert resp.status_code == 400


def test_appointment_accept(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    appointment_update_mock: MockType,
    fake_appointment,
    fake_tutor,
):
    client = setup_test
    apt = fake_appointment

    # login as tutor
    client.post(
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

    resp = client.put(
        "/appointment/accept", json={"id": fake_appointment.id, "accept": True}
    )
    appointment_update_mock.assert_called()

    assert resp.status_code == 200
    assert resp.json["id"] == apt.id
    assert resp.json["startTime"] == apt.startTime.isoformat()
    assert resp.json["endTime"] == apt.endTime.isoformat()
    assert resp.json["studentId"] == apt.studentId
    assert resp.json["tutorId"] == apt.tutorId
    assert resp.json["tutorAccepted"] == True


############################## REQUEST TESTS ###################################


def test_request_args(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_student: User,
    fake_tutor: User,
    fake_appointment: Appointment,
):
    client = setup_test

    # No JSON Body
    resp = client.post("/appointment/request")
    assert resp.json == {"error": "content-type was not json or data was malformed"}
    assert resp.status_code == 415

    # No logged in user
    resp = client.post("/appointment/request", json={})
    assert resp.json == {"error": "No user is logged in"}
    assert resp.status_code == 401

    client.post(
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

    # Missing start time
    resp = client.post("/appointment/request", json={})
    assert resp.json == {"error": "startTime field was missing"}
    assert resp.status_code == 400

    # Missing end time
    resp = client.post(
        "/appointment/request", json={"startTime": "2023-10-20T00:00:00+00:00"}
    )
    assert resp.json == {"error": "endTime field was missing"}
    assert resp.status_code == 400

    # Missing tutor id
    resp = client.post(
        "/appointment/request",
        json={
            "startTime": "2024-10-20T00:00:00+00:00",
            "endTime": "2024-10-20T01:00:00+00:00",
        },
    )
    assert resp.json == {"error": "Tutor id field was missing"}
    assert resp.status_code == 400

    # Invalid time (invalid start time format)
    resp = client.post(
        "/appointment/request",
        json={
            "startTime": "2023",
            "endTime": "2024-10-20T01:00:00+00:00",
            "tutorId": "1",
        },
    )
    assert resp.json == {"error": "startTime and/or endTime field(s) was malformed"}
    assert resp.status_code == 400

    # Invalid time (invalid end time format)
    resp = client.post(
        "/appointment/request",
        json={
            "startTime": "2024-10-20T00:00:00+00:00",
            "endTime": "2023",
            "tutorId": "1",
        },
    )
    assert resp.json == {"error": "startTime and/or endTime field(s) was malformed"}
    assert resp.status_code == 400

    # Invalid time (invalid both time format)
    resp = client.post(
        "/appointment/request",
        json={
            "startTime": "2023",
            "endTime": "2024",
            "tutorId": "1",
        },
    )
    assert resp.json == {"error": "startTime and/or endTime field(s) was malformed"}
    assert resp.status_code == 400

    # Invalid end time (et < st)
    resp = client.post(
        "/appointment/request",
        json={
            "startTime": "2024-10-20T01:00:00+00:00",
            "endTime": "2024-10-20T00:00:00+00:00",
            "tutorId": "1",
        },
    )
    assert resp.json == {"error": "endTime cannot be less than startTime"}
    assert resp.status_code == 400

    # Invalid start time (st > now)
    resp = client.post(
        "/appointment/request",
        json={
            "startTime": "2022-10-20T01:00:00+00:00",
            "endTime": "2024-10-20T00:00:00+00:00",
            "tutorId": "1",
        },
    )
    assert resp.json == {"error": "startTime must be in the future"}
    assert resp.status_code == 400

    # Invalid tutor id
    resp = client.post(
        "/appointment/request",
        json={
            "startTime": "2024-11-20T00:00:00+00:00",
            "endTime": "2024-11-20T01:00:00+00:00",
            "tutorId": "1",
        },
    )
    assert resp.json == {"error": "Tutor profile does not exist"}
    assert resp.status_code == 400

    client.post("/logout")
    client.post(
        "/login",
        json={
            "email": "validemail2@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )

    # Invalid user (tutor is logged in)
    resp = client.post(
        "/appointment/request",
        json={
            "startTime": "2024-10-20T00:00:00+00:00",
            "endTime": "2024-10-20T01:00:00+00:00",
            "tutorId": fake_tutor.id,
        },
    )
    assert resp.json == {"error": "Profile is not a student"}
    assert resp.status_code == 400

    client.post("/logout")
    client.post(
        "/login",
        json={
            "email": "validemail3@mail.com",
            "password": "12345678",
            "accountType": "admin",
        },
    )

    # Invalid user (admin is logged in)
    resp = client.post(
        "/appointment/request",
        json={
            "startTime": "2024-10-20T00:00:00+00:00",
            "endTime": "2024-10-20T01:00:00+00:00",
            "tutorId": fake_tutor.id,
        },
    )
    assert resp.json == {"error": "Profile is not a student"}
    assert resp.status_code == 400

    client.post("/logout")
    client.post(
        "/login",
        json={
            "email": "validemail@mail.com",
            "password": "12345678",
            "accountType": "student",
        },
    )

    create_mock = mocker.patch("tests.conftest.AppointmentActions.create")
    create_mock.return_value = fake_appointment

    # Valid Input
    resp = client.post(
        "/appointment/request",
        json={
            "startTime": "2024-10-20T00:00:00+00:00",
            "endTime": "2024-10-21T00:00:00+00:00",
            "tutorId": fake_tutor.id,
        },
    )

    # mocker.stop(create_mock)

    assert resp.status_code == 200
    assert resp.json["startTime"] == "2024-10-20T00:00:00+00:00"
    assert resp.json["endTime"] == "2024-10-21T00:00:00+00:00"
    assert resp.json["studentId"] == fake_student.id
    assert resp.json["tutorId"] == fake_tutor.id
    assert resp.json["tutorAccepted"] == False


############################### DELETE TESTS ###################################


def test_delete_args(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock,
    fake_tutor2: User,
    fake_appointment: Appointment,
):
    client = setup_test

    # No JSON Body
    resp = client.delete("/appointment")
    assert resp.json == {"error": "content-type was not json or data was malformed"}
    assert resp.status_code == 415

    # No logged in user
    resp = client.delete("/appointment", json={})
    assert resp.json == {"error": "No user is logged in"}
    assert resp.status_code == 401

    client.post(
        "/login",
        json={
            "email": fake_tutor2.email,
            "password": "12345678",
            "accountType": "tutor",
        },
    )

    find_unique_users_mock.assert_called_with(
        where={"email": fake_tutor2.email}, include=mocker.ANY
    )

    # Missing id
    resp = client.delete("/appointment", json={})
    assert resp.json == {"error": "id field was missing"}
    assert resp.status_code == 400

    resp = client.delete("/appointment", json={"id": "123"})
    assert resp.json == {"error": "Appointment does not exist"}
    assert resp.status_code == 404

    find = mocker.patch("tests.conftest.AppointmentActions.find_unique")
    find.return_value = fake_appointment

    delete = mocker.patch("tests.conftest.AppointmentActions.delete")
    resp = client.delete("/appointment", json={"id": fake_appointment.id})
    delete.assert_called()

    assert resp.status_code == 200
    assert resp.json["success"] == True


############################### MODIFY TESTS ###################################


def test_modify_args(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock,
    fake_tutor2: User,
    fake_appointment: Appointment,
):
    client = setup_test

    # No JSON Body
    resp = client.put("/appointment")
    assert resp.json == {"error": "content-type was not json or data was malformed"}
    assert resp.status_code == 415

    # No logged in user
    resp = client.put("/appointment", json={})
    assert resp.json == {"error": "No user is logged in"}
    assert resp.status_code == 401

    client.post(
        "/login",
        json={
            "email": fake_tutor2.email,
            "password": "12345678",
            "accountType": "tutor",
        },
    )

    find_unique_users_mock.assert_called_with(
        where={"email": fake_tutor2.email}, include=mocker.ANY
    )

    # Missing id
    resp = client.put("/appointment", json={})
    assert resp.json == {"error": "id field was missing"}
    assert resp.status_code == 400

    # Missing start time
    resp = client.put("/appointment", json={"id": "123"})
    assert resp.json == {"error": "startTime field was missing"}
    assert resp.status_code == 400

    # Missing end time
    resp = client.put(
        "/appointment", json={"id": "123", "startTime": "2023-10-20T00:00:00+00:00"}
    )
    assert resp.json == {"error": "endTime field was missing"}
    assert resp.status_code == 400

    # Invalid time (invalid start time format)
    resp = client.put(
        "/appointment",
        json={
            "id": "123",
            "startTime": "2023",
            "endTime": "2024-10-20T01:00:00+00:00",
        },
    )
    assert resp.json == {"error": "startTime and/or endTime field(s) was malformed"}
    assert resp.status_code == 400

    # Invalid time (invalid end time format)
    resp = client.put(
        "/appointment",
        json={
            "id": "123",
            "startTime": "2024-10-20T00:00:00+00:00",
            "endTime": "2023",
        },
    )
    assert resp.json == {"error": "startTime and/or endTime field(s) was malformed"}
    assert resp.status_code == 400

    # Invalid time (invalid both time format)
    resp = client.put(
        "/appointment",
        json={
            "id": "123",
            "startTime": "2023",
            "endTime": "2024",
        },
    )
    assert resp.json == {"error": "startTime and/or endTime field(s) was malformed"}
    assert resp.status_code == 400

    # Invalid end time (et < st)
    resp = client.put(
        "/appointment",
        json={
            "id": "123",
            "startTime": "2024-10-20T01:00:00+00:00",
            "endTime": "2024-10-20T00:00:00+00:00",
        },
    )
    assert resp.json == {"error": "endTime cannot be less than startTime"}
    assert resp.status_code == 400

    # Invalid start time (st > now)
    resp = client.put(
        "/appointment",
        json={
            "id": "123",
            "startTime": "2022-10-20T01:00:00+00:00",
            "endTime": "2024-10-20T00:00:00+00:00",
        },
    )
    assert resp.json == {"error": "startTime must be in the future"}
    assert resp.status_code == 400

    # Invalid tutor id
    resp = client.put(
        "/appointment",
        json={
            "id": "123",
            "startTime": "2024-11-20T00:00:00+00:00",
            "endTime": "2024-11-20T01:00:00+00:00",
        },
    )
    assert resp.json == {"error": "Appointment does not exist"}
    assert resp.status_code == 404

    find = mocker.patch("tests.conftest.AppointmentActions.find_unique")
    find.return_value = fake_appointment

    update = mocker.patch("tests.conftest.AppointmentActions.update")
    resp = client.put(
        "/appointment",
        json={
            "id": fake_appointment.id,
            "startTime": "2024-11-20T00:00:00+00:00",
            "endTime": "2024-11-20T01:00:00+00:00",
        },
    )
    update.assert_called()
    assert resp.json == {"success": True}
    assert resp.status_code == 200


############################### RATING TESTS ###################################


def test_rating_args(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock,
    fake_student: User,
    fake_appointment_fin: Appointment,
    fake_rating: Rating,
):
    client = setup_test

    # No JSON Body
    resp = client.post("/appointment/rating")
    assert resp.json == {"error": "content-type was not json or data was malformed"}
    assert resp.status_code == 415

    # No logged in user
    resp = client.post("/appointment/rating", json={})
    assert resp.json == {"error": "No user is logged in"}
    assert resp.status_code == 401

    client.post(
        "/login",
        json={
            "email": fake_student.email,
            "password": "12345678",
            "accountType": "student",
        },
    )

    find_unique_users_mock.assert_called_with(
        where={"email": fake_student.email}, include=mocker.ANY
    )

    # Missing id
    resp = client.post("/appointment/rating", json={})
    assert resp.json == {"error": "id field was missing"}
    assert resp.status_code == 400

    # Missing rating field
    resp = client.post("/appointment/rating", json={"id": "123"})
    assert resp.json == {"error": "rating field was missing"}
    assert resp.status_code == 400

    resp = client.post("/appointment/rating", json={"id": "123", "rating": 5})
    assert resp.json == {"error": "Appointment does not exist"}
    assert resp.status_code == 400

    rating = mocker.patch("tests.conftest.AppointmentActions.find_unique")
    rating.return_value = fake_appointment_fin

    resp = client.post(
        "/appointment/rating", json={"id": fake_appointment_fin.id, "rating": 10}
    )
    assert resp.json == {"error": "Rating must be between 1 and 5"}
    assert resp.status_code == 400

    create = mocker.patch("tests.conftest.RatingActions.create")
    create.return_value = fake_rating

    resp = client.post(
        "/appointment/rating", json={"id": fake_appointment_fin.id, "rating": 5}
    )
    assert resp.status_code == 200
    assert resp.json["success"] == True
