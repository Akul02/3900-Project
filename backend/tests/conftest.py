import pytest
from datetime import datetime
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType
from hashlib import sha256
from uuid import uuid4
from flask.testing import FlaskClient
from prisma.cli import prisma
import prisma.models as models
import subprocess
import sys
import os
from pathlib import Path

# unused import for mocking purposes during tests
from prisma.actions import (
    UserActions,
    TutorActions,
    SubjectActions,
    AdminActions,
    StudentActions,
    AppointmentActions,
    RatingActions,
)

# hack to import a root level file and be able to run pytest from any dir
# source: https://www.geeksforgeeks.org/python-import-from-parent-directory/
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from app import app

# basic testing utils ##########################################################


@pytest.fixture
def setup_test():
    return app.test_client()


@pytest.fixture(scope="session", autouse=True)
def cleanup():
    yield None
    # check is probably unnecssary, but better to be safe than sorry
    if Path.cwd().parts[-1] == "tests" and (Path.cwd() / "flask_session").is_dir():
        subprocess.run(["rm", "-rf", "flask_session"])


# ? Probably no longer necessary due to additional of mocking
def test_setup_test_db(setup_test):
    try:
        # check that all tables are empty
        assert models.Admin.prisma().count() == 0
        assert models.Student.prisma().count() == 0
        assert models.Tutor.prisma().count() == 0
        assert models.Subject.prisma().count() == 0
        assert models.TutorAvailability.prisma().count() == 0
        assert models.Rating.prisma().count() == 0
        assert models.Appointment.prisma().count() == 0
    except prisma.errors.ClientNotRegisteredError:
        assert False, "Model Based Access is not functional"


def test_setup_test_client(setup_test: FlaskClient):
    client = setup_test
    response = client.get("/")
    assert response.data == b"Hello world!"
    assert response.status_code == 200


# mocks / fake data ############################################################


# ! Note: Assumes a db of exactly one fake admin, student, and tutor
# with the ids and emails of the 'fake' admin, student, user
# such, if tests rely on removal/addition of these cases this will not work
@pytest.fixture
def find_unique_users_mock(
    mocker: MockerFixture, fake_student, fake_admin, fake_tutor, fake_tutor2
) -> MockType:
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
        elif ("id" in kwargs["where"] and kwargs["where"]["id"] == fake_tutor.id) or (
            "email" in kwargs["where"] and kwargs["where"]["email"] == fake_tutor.email
        ):
            return fake_tutor
        elif ("id" in kwargs["where"] and kwargs["where"]["id"] == fake_tutor2.id) or (
            "email" in kwargs["where"] and kwargs["where"]["email"] == fake_tutor2.email
        ):
            return fake_tutor2

        return None

    return mocker.patch(
        "tests.conftest.UserActions.find_unique",
        new=mocker.Mock(side_effect=mocked_find_unique),
    )


@pytest.fixture
def find_many_tutors_mock(mocker: MockerFixture) -> MockType:
    return mocker.patch("tests.conftest.TutorActions.find_many")


@pytest.fixture
def find_many_users_mock(mocker: MockerFixture) -> MockType:
    return mocker.patch("tests.conftest.UserActions.find_many")


@pytest.fixture
def find_many_students_mock(mocker: MockerFixture) -> MockType:
    return mocker.patch("tests.conftest.StudentActions.find_many")


@pytest.fixture
def find_many_admins_mock(mocker: MockerFixture) -> MockType:
    return mocker.patch("tests.conftest.AdminActions.find_many")


@pytest.fixture
def fake_user():
    def __fake_user(email: str, pword: str, type: str) -> models.User:
        id = str(uuid4())
        match type.lower():
            case "student":
                user = models.User(
                    id=id,
                    name="name",
                    email=email,
                    hashedPassword=sha256(pword.encode()).hexdigest(),
                    studentInfo=models.Student(id=id, userInfoId=id),
                )
                user.studentInfo = models.Student(id=id, userInfoId=id, userInfo=user)
                return user
            case "tutor":
                user = models.User(
                    id=id,
                    name="name",
                    email=email,
                    hashedPassword=sha256(pword.encode()).hexdigest(),
                    tutorInfo=models.Tutor(id=id, userInfoId=id),
                )
                user.tutorInfo = models.Tutor(id=id, userInfoId=id, userInfo=user)
                return user
            case "admin":
                user = models.User(
                    id=id,
                    name="name",
                    email=email,
                    hashedPassword=sha256(pword.encode()).hexdigest(),
                    adminInfo=models.Admin(id=id, userInfoId=id),
                )
                user.adminInfo = models.Admin(id=id, userInfoId=id, userInfo=user)
                return user
            case _:
                return models.User(
                    id=id, name="name", email=email, hashedPassword=pword
                )

    return __fake_user


@pytest.fixture
def fake_student(fake_user) -> models.User:
    return fake_user("validemail@mail.com", "12345678", "student")


@pytest.fixture
def fake_tutor(fake_user) -> models.User:
    return fake_user("validemail2@mail.com", "12345678", "tutor")


@pytest.fixture
def fake_tutor2(fake_user, fake_appointment) -> models.User:
    fake_tutor = fake_user("validemail4@mail.com", "12345678", "tutor")
    fake_tutor.tutorInfo.appointments = [fake_appointment]
    return fake_tutor


@pytest.fixture
def fake_admin(fake_user) -> models.User:
    return fake_user("validemail3@mail.com", "12345678", "admin")


@pytest.fixture
def fake_appointment(fake_tutor, fake_student):
    apt = models.Appointment(
        id=str(uuid4()),
        startTime="2024-10-20T00:00:00+00:00",
        endTime="2024-10-21T00:00:00+00:00",
        tutorAccepted=False,
        tutor=fake_tutor.tutorInfo,
        tutorId=fake_tutor.id,
        student=fake_student.studentInfo,
        studentId=fake_student.id,
    )

    return apt


@pytest.fixture
def fake_appointment_fin(fake_tutor, fake_student):
    apt = models.Appointment(
        id=str(uuid4()),
        startTime="2023-10-20T00:00:00+00:00",
        endTime="2023-10-21T00:00:00+00:00",
        tutorAccepted=False,
        tutor=fake_tutor.tutorInfo,
        tutorId=fake_tutor.id,
        student=fake_student.studentInfo,
        studentId=fake_student.id,
    )

    return apt


@pytest.fixture
def fake_rating(fake_appointment):
    rating = models.Rating(
        id=str(uuid4()),
        score=5,
        appointment=fake_appointment,
        appointmentId=fake_appointment.id,
        createdFor=fake_appointment.tutor,
        tutorId=fake_appointment.tutorId,
    )

    return rating
