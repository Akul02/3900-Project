import pytest
from pytest_mock import MockerFixture
from uuid import uuid4
from flask.testing import FlaskClient
from prisma.models import Subject, User, TutorAvailability, Appointment, Rating
from datetime import datetime, timedelta, timezone
from pytest_mock.plugin import MockType


@pytest.fixture
def generate_tutor(fake_tutor, fake_student) -> User:
    science = Subject(name="science")
    fake_tutor.email = "validemail2@mail.com"
    fake_tutor.name = "Terry"
    fake_tutor.bio = "band 1 at HSC Maths"
    fake_tutor.location = "Australia"
    fake_tutor.phoneNumber = "0411123901"
    apt = Appointment(
        id=str(uuid4()),
        startTime=datetime.now(timezone.utc),
        endTime=datetime.now(timezone.utc),
        tutorAccepted=False,
        tutor=fake_tutor.tutorInfo,
        tutorId=fake_tutor.id,
        student=fake_student.studentInfo,
        studentId=fake_student.id,
    )
    rating = Rating(
        id=str(uuid4()),
        score=2,
        appointment=apt,
        appointmentId=apt.id,
        createdFor=fake_tutor.tutorInfo,
        tutorId=fake_tutor.id,
    )
    apt.rating = rating
    fake_tutor.tutorInfo.appointments = [apt]
    fake_tutor.tutorInfo.ratings = [rating]
    fake_tutor.tutorInfo.courseOfferings = [science]

    return fake_tutor


@pytest.fixture
def custom_find_unique(
    mocker: MockerFixture, generate_tutor, fake_admin, fake_student
) -> User:
    def mocked_find_unique(**kwargs):
        # where must exist
        if ("id" in kwargs["where"] and kwargs["where"]["id"] == fake_admin.id) or (
            "email" in kwargs["where"] and kwargs["where"]["email"] == fake_admin.email
        ):
            return fake_admin
        elif ("id" in kwargs["where"] and kwargs["where"]["id"] == fake_student.id) or (
            "email" in kwargs["where"]
            and kwargs["where"]["email"] == fake_student.email
        ):
            return fake_student
        elif (
            "id" in kwargs["where"] and kwargs["where"]["id"] == generate_tutor.id
        ) or (
            "email" in kwargs["where"]
            and kwargs["where"]["email"] == generate_tutor.email
        ):
            return generate_tutor

        return None

    return mocker.patch(
        "tests.conftest.UserActions.find_unique",
        new=mocker.Mock(side_effect=mocked_find_unique),
    )


# Get Tutor Profile Tests


def test_get_missing_id(setup_test: FlaskClient):
    client = setup_test
    resp = client.get("/tutor/")
    # assert resp.json == {"error": "id field was missing"}
    assert resp.status_code == 405


def test_get_nonexisting_profile(setup_test: FlaskClient):
    client = setup_test
    resp = client.get("/tutor/1")
    assert resp.json == {"error": "Profile does not exist"}
    assert resp.status_code == 404


def test_get_valid(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    custom_find_unique: MockType,
    generate_tutor: User,
):
    client = setup_test

    tutor = generate_tutor

    resp = client.get(f"/tutor/{tutor.id}")
    custom_find_unique.assert_called_with(where={"id": tutor.id}, include=mocker.ANY)

    assert resp.status_code == 200
    assert resp.json["id"] == tutor.id
    assert resp.json["email"] == "validemail2@mail.com"
    assert resp.json["name"] == "Terry"
    assert resp.json["bio"] == "band 1 at HSC Maths"
    assert resp.json["rating"] == 2
    assert resp.json["location"] == "Australia"
    assert resp.json["profilePicture"] is None
    assert resp.json["phoneNumber"] == "0411123901"
    assert "science" in resp.json["courseOfferings"]
    assert len(resp.json["timesAvailable"]) == 0


# Modify Tutor Profile Tests


def test_modify_not_json(setup_test: FlaskClient):
    client = setup_test
    resp = client.put("/tutor/profile")
    assert resp.json == {"error": "content-type was not json or data was malformed"}
    assert resp.status_code == 415


def test_modify_invalid_args(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    custom_find_unique: MockType,
    generate_tutor: User,
    fake_admin: User,
):
    client = setup_test
    tutor = generate_tutor

    # No user logged in
    resp = client.put("/tutor/profile", json={})
    assert resp.json == {"error": "No user is logged in"}
    assert resp.status_code == 400

    resp = client.post(
        "/login",
        json={
            "email": "validemail2@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )
    custom_find_unique.assert_called_with(
        where={"email": tutor.email}, include=mocker.ANY
    )

    assert resp.status_code == 200

    # Non admin user tries modifying other user
    resp = client.put("/tutor/profile", json={"id": tutor.id})
    custom_find_unique.assert_called_with(where={"id": tutor.id}, include=mocker.ANY)
    assert resp.json == {"error": "id field should not be supplied by a non admin user"}
    assert resp.status_code == 403

    resp = client.post("/logout")
    assert resp.status_code == 200

    # admin logs in

    resp = client.post(
        "/login",
        json={
            "email": "validemail3@mail.com",
            "password": "12345678",
            "accountType": "admin",
        },
    )
    custom_find_unique.assert_called_with(
        where={"email": fake_admin.email}, include=mocker.ANY
    )
    assert resp.status_code == 200

    # admin tries to modify with giving id param
    resp = client.put("/tutor/profile", json={})
    assert resp.json == {"error": "id field was missing"}
    assert resp.status_code == 400

    custom_find_unique = None
    # admin modifies profile that doesnt exist
    resp = client.put("/tutor/profile", json={"id": "1"})
    assert resp.json == {"error": "Profile does not exist"}
    assert resp.status_code == 404


def test_modify_invalid_email(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    custom_find_unique: MockType,
    generate_tutor: User,
):
    client = setup_test
    tutor = generate_tutor

    resp = client.post(
        "/login",
        json={
            "email": "validemail2@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )
    custom_find_unique.assert_called_with(
        where={"email": tutor.email}, include=mocker.ANY
    )
    assert resp.status_code == 200

    resp = client.put(
        "/tutor/profile",
        json={
            "email": "validemailmail.com",
        },
    )

    assert resp.status_code == 400
    assert resp.json == {"error": "email field is invalid"}


def test_modify_missing_args(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    custom_find_unique: MockType,
    generate_tutor: User,
):
    client = setup_test
    tutor = generate_tutor

    resp = client.post(
        "/login",
        json={
            "email": "validemail2@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )
    custom_find_unique.assert_called_with(
        where={"email": tutor.email}, include=mocker.ANY
    )
    assert resp.status_code == 200

    # missing fields
    resp = client.put("/tutor/profile", json={})
    assert resp.status_code == 200

    resp = client.get(f"/tutor/{tutor.id}")
    assert resp.status_code == 200
    assert resp.json["id"] == tutor.id
    assert resp.json["email"] == "validemail2@mail.com"
    assert resp.json["name"] == "Terry"
    assert resp.json["bio"] == "band 1 at HSC Maths"
    assert resp.json["rating"] == 2
    assert resp.json["location"] == "Australia"
    assert resp.json["profilePicture"] is None
    assert resp.json["phoneNumber"] == "0411123901"
    assert "science" in resp.json["courseOfferings"]
    assert len(resp.json["timesAvailable"]) == 0


def test_modify_same_values(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    custom_find_unique: MockType,
    generate_tutor: User,
):
    client = setup_test
    tutor = generate_tutor

    resp = client.post(
        "/login",
        json={
            "email": "validemail2@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )
    custom_find_unique.assert_called_with(
        where={"email": tutor.email}, include=mocker.ANY
    )
    assert resp.status_code == 200

    update_user_mock = mocker.patch("tests.conftest.UserActions.update")
    update_tutor_mock = mocker.patch("tests.conftest.TutorActions.update")
    create_subject_mock = mocker.patch("tests.conftest.SubjectActions.create")
    # same values in fields
    resp = client.put(
        "/tutor/profile",
        json={
            "name": "Terry",
            "bio": "band 1 at HSC Maths",
            "email": "validemail2@mail.com",
            "profilePicture": None,
            "location": "Australia",
            "phoneNumber": "0411123901",
            "courseOfferings": ["science"],
            "timesAvailable": [],
        },
    )
    create_subject_mock.assert_called()
    update_tutor_mock.assert_called()
    update_user_mock.assert_called()
    assert resp.status_code == 200

    resp = client.get(f"/tutor/{tutor.id}")

    assert resp.status_code == 200
    assert resp.json["id"] == tutor.id
    assert resp.json["email"] == "validemail2@mail.com"
    assert resp.json["name"] == "Terry"
    assert resp.json["bio"] == "band 1 at HSC Maths"
    assert resp.json["rating"] == 2
    assert resp.json["location"] == "Australia"
    assert resp.json["profilePicture"] is None
    assert resp.json["phoneNumber"] == "0411123901"
    assert "science" in resp.json["courseOfferings"]
    assert len(resp.json["timesAvailable"]) == 0


def test_modify_different_values(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    custom_find_unique: MockType,
    generate_tutor: User,
):
    client = setup_test
    tutor = generate_tutor

    start_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
    end_time = (datetime.utcnow() + timedelta(days=2)).isoformat()

    resp = client.post(
        "/login",
        json={
            "email": "validemail2@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )
    custom_find_unique.assert_called_with(
        where={"email": tutor.email}, include=mocker.ANY
    )
    assert resp.status_code == 200

    update_user_mock = mocker.patch("tests.conftest.UserActions.update")
    update_tutor_mock = mocker.patch("tests.conftest.TutorActions.update")
    create_subject_mock = mocker.patch("tests.conftest.SubjectActions.create")
    resp = client.put(
        "/tutor/profile",
        json={
            "name": "Juan",
            "bio": "band 6 at HSC Maths",
            "email": "valid@mail.com",
            "profilePicture": "",
            "location": "Sydney",
            "phoneNumber": "0411123888",
            "courseOfferings": ["science", "math"],
            "timesAvailable": [{"startTime": start_time, "endTime": end_time}],
        },
    )
    update_tutor_mock.assert_called()
    update_user_mock.assert_called()
    create_subject_mock.assert_called()
    assert resp.status_code == 200

    mocker.stop(custom_find_unique)
    find_unique_mock = mocker.patch("tests.conftest.UserActions.find_unique")
    find_unique_mock.return_value = tutor
    tutor.name = "Juan"
    tutor.bio = "band 6 at HSC Maths"
    tutor.email = "valid@mail.com"
    tutor.profilePicture = ""
    tutor.location = "Sydney"
    tutor.phoneNumber = "0411123888"
    tutor.tutorInfo.courseOfferings = [Subject(name="science"), Subject(name="math")]
    tutor.tutorInfo.timesAvailable = [
        TutorAvailability(
            id="1",
            tutor=tutor.tutorInfo,
            tutorId=tutor.id,
            startTime=start_time,
            endTime=end_time,
        )
    ]

    resp = client.get(f"/tutor/{tutor.id}")
    assert resp.status_code == 200

    assert resp.json["id"] == tutor.id
    assert resp.json["email"] == "valid@mail.com"
    assert resp.json["name"] == "Juan"
    assert resp.json["bio"] == "band 6 at HSC Maths"
    assert resp.json["rating"] == 2
    assert resp.json["location"] == "Sydney"
    assert resp.json["profilePicture"] == ""
    assert resp.json["phoneNumber"] == "0411123888"
    assert (
        "science" in resp.json["courseOfferings"]
        and "math" in resp.json["courseOfferings"]
    )
    assert len(resp.json["timesAvailable"]) == 1

    response = datetime.fromisoformat(
        resp.json["timesAvailable"][0]["startTime"]
    ).replace(tzinfo=None, minute=0, second=0, microsecond=0)
    expected = datetime.fromisoformat(start_time).replace(
        minute=0, second=0, microsecond=0
    )
    assert response == expected

    response = datetime.fromisoformat(
        resp.json["timesAvailable"][0]["endTime"]
    ).replace(tzinfo=None, minute=0, second=0, microsecond=0)
    expected = datetime.fromisoformat(end_time).replace(
        minute=0, second=0, microsecond=0
    )
    assert response == expected


# Delete Profile Tests


def test_delete_not_json(setup_test: FlaskClient):
    client = setup_test
    resp = client.delete("/tutor/")
    assert resp.json == {"error": "content-type was not json or data was malformed"}
    assert resp.status_code == 415


def test_delete_no_user(setup_test: FlaskClient):
    client = setup_test
    resp = client.delete("/tutor/", json={})
    assert resp.json == {"error": "No user is logged in"}
    assert resp.status_code == 400


def test_delete_permission(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    custom_find_unique: MockType,
    generate_tutor: User,
):
    client = setup_test
    tutor = generate_tutor

    resp = client.post(
        "/login",
        json={
            "email": "validemail2@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )
    custom_find_unique.assert_called_with(
        where={"email": tutor.email}, include=mocker.ANY
    )
    assert resp.status_code == 200

    resp = client.delete("/tutor/", json={"id": tutor.id})

    assert resp.json == {"error": "id field should not be supplied by a non admin user"}
    assert resp.status_code == 403


def test_delete_nonexisting_profile(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    custom_find_unique: MockType,
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
    custom_find_unique.assert_called_with(
        where={"email": fake_admin.email}, include=mocker.ANY
    )
    assert resp.status_code == 200

    resp = client.delete("/tutor/", json={"id": "1"})
    # admin_view_mock.assert_called_with(id=fake_admin.id)
    custom_find_unique.assert_called_with(where={"id": "1"}, include=mocker.ANY)

    assert resp.status_code == 404
    assert resp.json == {"error": "Profile does not exist"}


def test_delete_valid(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    custom_find_unique: MockType,
    generate_tutor: User,
):
    client = setup_test
    tutor = generate_tutor

    resp = client.post(
        "/login",
        json={
            "email": "validemail2@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )
    custom_find_unique.assert_called_with(
        where={"email": tutor.email}, include=mocker.ANY
    )
    assert resp.status_code == 200

    delete_mock = mocker.patch("tests.conftest.UserActions.delete")
    resp = client.delete("/tutor/", json={})
    delete_mock.assert_called()

    assert resp.status_code == 200

    mocker.stop(custom_find_unique)
    find_unique_mocker = mocker.patch("tests.conftest.UserActions.find_unique")
    find_unique_mocker.return_value = None

    resp = client.get(f"/tutor/{tutor.id}")
    assert resp.json == {"error": "Profile does not exist"}
    assert resp.status_code == 404


def test_modify_time_available(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    custom_find_unique: MockType,
    generate_tutor: User,
):
    client = setup_test
    tutor = generate_tutor

    start_time1 = datetime.now() + timedelta(days=1)
    end_time1 = datetime.now() + timedelta(days=2)

    start_time2 = datetime.now() + timedelta(days=3)
    end_time2 = datetime.now() + timedelta(days=4)

    resp = client.post(
        "/login",
        json={
            "email": "validemail2@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )
    custom_find_unique.assert_called_with(
        where={"email": tutor.email}, include=mocker.ANY
    )
    assert resp.status_code == 200

    # malformed timesAvailable
    resp = client.put(
        "/tutor/profile",
        json={
            "timesAvailable": [
                {
                    "endTime": end_time1.isoformat(),
                },
                {
                    "startTime": start_time2.isoformat(),
                },
            ],
        },
    )
    assert resp.status_code == 400
    assert resp.json["error"] == "'startTime' was missing from timesAvailable"

    update_user_mock = mocker.patch("tests.conftest.UserActions.update")
    update_tutor_mock = mocker.patch("tests.conftest.TutorActions.update")
    # valid modification
    resp = client.put(
        "/tutor/profile",
        json={
            "timesAvailable": [
                {
                    "startTime": start_time1.isoformat(),
                    "endTime": end_time1.isoformat(),
                },
                {
                    "startTime": start_time2.isoformat(),
                    "endTime": end_time2.isoformat(),
                },
            ],
        },
    )
    custom_find_unique.assert_called_with(where={"id": tutor.id}, include=mocker.ANY)
    update_user_mock.assert_called()
    update_tutor_mock.assert_called()
    assert resp.status_code == 200

    tutor.tutorInfo.timesAvailable = [
        TutorAvailability(
            id="1",
            tutor=tutor.tutorInfo,
            tutorId=tutor.id,
            startTime=start_time1,
            endTime=end_time1,
        ),
        TutorAvailability(
            id="2",
            tutor=tutor.tutorInfo,
            tutorId=tutor.id,
            startTime=start_time2,
            endTime=end_time2,
        ),
    ]

    # overlapping time availabilities
    resp = client.put(
        "/tutor/profile",
        json={
            "timesAvailable": [
                {
                    "startTime": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                    "endTime": (datetime.utcnow() + timedelta(days=2)).isoformat(),
                },
                {
                    "startTime": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                    "endTime": (datetime.utcnow() + timedelta(days=5)).isoformat(),
                },
            ],
        },
    )
    custom_find_unique.assert_called_with(where={"id": tutor.id}, include=mocker.ANY)
    assert resp.status_code == 400
    assert resp.json["error"] == "Time availabilities should not overlap"

    resp = client.get(f"/tutor/{tutor.id}")
    custom_find_unique.assert_called_with(where={"id": tutor.id}, include=mocker.ANY)

    assert resp.status_code == 200
    assert len(resp.json["timesAvailable"]) == 2
    assert resp.json["timesAvailable"][0]["startTime"] == start_time1.isoformat()
    assert resp.json["timesAvailable"][0]["endTime"] == end_time1.isoformat()
    assert resp.json["timesAvailable"][1]["startTime"] == start_time2.isoformat()
    assert resp.json["timesAvailable"][1]["endTime"] == end_time2.isoformat()
