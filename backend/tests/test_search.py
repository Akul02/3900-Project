from typing import List
import pytest
import json
from flask.testing import FlaskClient
from prisma.models import Subject, User, Tutor, Appointment, Rating, TutorAvailability
from datetime import datetime, timedelta, timezone
from pytest_mock.plugin import MockType


@pytest.fixture
def generate_fake_tutors(fake_user) -> List[Tutor]:
    math = Subject(name="math")
    science = Subject(name="science")

    fake_student: User = fake_user("dummy@student.com", "1234678", "student")

    # first tutor
    tutor1: User = fake_user("mail@gmail.com", "12345678", "tutor")
    tutor1.location = "Australia"
    tutor1.name = "James"
    tutor1.tutorInfo.courseOfferings = [math]
    tutor1.tutorInfo.userInfo = tutor1
    apt1 = Appointment(
        id="1",
        startTime=datetime.now(timezone.utc),
        endTime=datetime.now(timezone.utc),
        tutor=tutor1.tutorInfo,
        tutorId=tutor1.id,
        student=fake_student.studentInfo,
        studentId=fake_student.id,
        tutorAccepted=False,
    )
    rating1 = Rating(
        id="1",
        score=2,
        appointment=apt1,
        appointmentId=apt1.id,
        createdFor=tutor1.tutorInfo,
        tutorId=tutor1.id,
    )
    tutor1.tutorInfo.timesAvailable = []
    apt1.rating = rating1
    tutor1.tutorInfo.ratings = [rating1]
    tutor1.tutorInfo.appointments = [apt1]

    # second tutor
    tutor2: User = fake_user("mail@gmail.com", "12345678", "tutor")
    tutor2.location = "Tasmania"
    tutor2.name = "Jan"
    tutor2.tutorInfo.courseOfferings = [science]
    tutor2.tutorInfo.userInfo = tutor2
    apt2 = Appointment(
        id="2",
        startTime=datetime.now(timezone.utc),
        endTime=datetime.now(timezone.utc),
        tutor=tutor2.tutorInfo,
        tutorId=tutor2.id,
        student=fake_student.studentInfo,
        studentId=fake_student.id,
        tutorAccepted=False,
    )
    rating2 = Rating(
        id="2",
        score=4,
        appointment=apt2,
        appointmentId=apt2.id,
        createdFor=tutor2.tutorInfo,
        tutorId=tutor2.id,
    )
    timesAvailable1 = TutorAvailability(
        id="1",
        tutor=tutor2.tutorInfo,
        tutorId=tutor2.id,
        startTime=datetime.now(timezone.utc) + timedelta(days=4, hours=0),
        endTime=datetime.now(timezone.utc) + timedelta(days=4, hours=6),
    )
    tutor2.tutorInfo.timesAvailable = [timesAvailable1]
    apt2.rating = rating2
    tutor2.tutorInfo.ratings = [rating2]
    tutor2.tutorInfo.appointments = [apt2]

    # third tutor
    tutor3: User = fake_user("mail@gmail.com", "12345678", "tutor")
    tutor3.location = "Tasmania"
    tutor3.name = "John"
    tutor3.tutorInfo.courseOfferings = [math, science]
    tutor3.tutorInfo.userInfo = tutor3
    apt3 = Appointment(
        id="3",
        startTime=datetime.now(timezone.utc),
        endTime=datetime.now(timezone.utc),
        tutor=tutor3.tutorInfo,
        tutorId=tutor3.id,
        student=fake_student.studentInfo,
        studentId=fake_student.id,
        tutorAccepted=False,
    )
    rating3 = Rating(
        id="3",
        score=3,
        appointment=apt3,
        appointmentId=apt3.id,
        createdFor=tutor3.tutorInfo,
        tutorId=tutor3.id,
    )
    timesAvailable2 = TutorAvailability(
        id="2",
        tutor=tutor3.tutorInfo,
        tutorId=tutor3.id,
        startTime=datetime.now(timezone.utc) + timedelta(days=3, hours=0),
        endTime=datetime.now(timezone.utc) + timedelta(days=3, hours=6),
    )
    tutor3.tutorInfo.timesAvailable = [timesAvailable2]
    apt3.rating = rating3
    tutor3.tutorInfo.appointments = [apt3]
    tutor3.tutorInfo.ratings = [rating3]

    return tutor1.tutorInfo, tutor2.tutorInfo, tutor3.tutorInfo


def test_search_no_args(
    setup_test: FlaskClient,
    find_many_tutors_mock: MockType,
    generate_fake_tutors: List[Tutor],
):
    client = setup_test

    tutor1, tutor2, tutor3 = generate_fake_tutors
    find_many_tutors_mock.return_value = [tutor1, tutor2, tutor3]

    resp = client.get("/searchtutor", query_string={})

    find_many_tutors_mock.assert_called()

    assert "tutorIds" in resp.json
    assert len(resp.json["tutorIds"]) == 3
    assert resp.status_code == 200
    assert all(id in [tutor1.id, tutor2.id, tutor3.id] for id in resp.json["tutorIds"])


def test_search_only_name(
    setup_test: FlaskClient,
    find_many_tutors_mock: MockType,
    generate_fake_tutors: List[User],
):
    client = setup_test

    tutor1, tutor2, tutor3 = generate_fake_tutors
    find_many_tutors_mock.return_value = [tutor1, tutor2, tutor3]

    # only name
    resp = client.get("/searchtutor", query_string={"name": "James"})
    find_many_tutors_mock.assert_called()

    assert resp.status_code == 200
    assert len(resp.json["tutorIds"]) == 1
    assert resp.json["tutorIds"][0] == tutor1.id


def test_search_only_location(
    setup_test: FlaskClient,
    find_many_tutors_mock: MockType,
    generate_fake_tutors: List[Tutor],
):
    client = setup_test

    tutor1, tutor2, tutor3 = generate_fake_tutors
    find_many_tutors_mock.return_value = [tutor1, tutor2, tutor3]

    # only location
    resp = client.get("/searchtutor", query_string={"location": "Tasmania"})
    find_many_tutors_mock.assert_called()

    assert len(resp.json["tutorIds"]) == 2
    assert resp.status_code == 200
    assert all(id in [tutor2.id, tutor3.id] for id in resp.json["tutorIds"])

    resp = client.get("/searchtutor", query_string={"location": "Australia"})
    find_many_tutors_mock.assert_called()

    assert len(resp.json["tutorIds"]) == 1
    assert resp.status_code == 200
    assert resp.json["tutorIds"][0] == tutor1.id


def test_search_only_ratings(
    setup_test: FlaskClient,
    find_many_tutors_mock: MockType,
    generate_fake_tutors: List[Tutor],
):
    client = setup_test

    tutor1, tutor2, tutor3 = generate_fake_tutors
    find_many_tutors_mock.return_value = [tutor1, tutor2, tutor3]

    # only rating
    resp = client.get("/searchtutor", query_string={"rating": 2})
    find_many_tutors_mock.assert_called()

    assert len(resp.json["tutorIds"]) == 3
    assert resp.status_code == 200
    assert all(id in [tutor1.id, tutor2.id, tutor3.id] for id in resp.json["tutorIds"])

    resp = client.get("/searchtutor", query_string={"rating": 3})
    find_many_tutors_mock.assert_called()

    assert len(resp.json["tutorIds"]) == 2
    assert resp.status_code == 200
    assert all(id in [tutor2.id, tutor3.id] for id in resp.json["tutorIds"])

    resp = client.get("/searchtutor", query_string={"rating": 4})
    find_many_tutors_mock.assert_called()

    assert len(resp.json["tutorIds"]) == 1
    assert resp.status_code == 200
    assert resp.json["tutorIds"][0] == tutor2.id


def test_search_only_course_offerings(
    setup_test: FlaskClient,
    find_many_tutors_mock: MockType,
    generate_fake_tutors: List[Tutor],
):
    client = setup_test

    tutor1, tutor2, tutor3 = generate_fake_tutors
    find_many_tutors_mock.return_value = [tutor1, tutor2, tutor3]

    # only courseOfferings
    resp = client.get(
        "/searchtutor", query_string={"courseOfferings": json.dumps(["math"])}
    )
    find_many_tutors_mock.assert_called()

    assert len(resp.json["tutorIds"]) == 2
    assert resp.status_code == 200
    assert all(id in [tutor1.id, tutor3.id] for id in resp.json["tutorIds"])

    resp = client.get(
        "/searchtutor", query_string={"courseOfferings": json.dumps(["science"])}
    )
    find_many_tutors_mock.assert_called()

    assert len(resp.json["tutorIds"]) == 2
    assert resp.status_code == 200
    assert all(id in [tutor2.id, tutor3.id] for id in resp.json["tutorIds"])

    resp = client.get(
        "/searchtutor",
        query_string={"courseOfferings": json.dumps(["math", "science"])},
    )
    find_many_tutors_mock.assert_called()

    assert len(resp.json["tutorIds"]) == 3
    assert resp.status_code == 200
    assert all(id in [tutor1.id, tutor2.id, tutor3.id] for id in resp.json["tutorIds"])


def test_search_only_time_range(
    setup_test: FlaskClient,
    find_many_tutors_mock: MockType,
    generate_fake_tutors: List[Tutor],
):
    client = setup_test

    tutor1, tutor2, tutor3 = generate_fake_tutors
    find_many_tutors_mock.return_value = [tutor1, tutor2, tutor3]

    # only timeRange
    resp = client.get(
        "/searchtutor",
        query_string={
            "timeRange": json.dumps(
                {
                    "startTime": (datetime.now() + timedelta(hours=1)).isoformat(),
                    "endTime": (datetime.now() + timedelta(days=10)).isoformat(),
                }
            )
        },
    )
    find_many_tutors_mock.assert_called()

    assert resp.status_code == 200
    assert len(resp.json["tutorIds"]) == 2
    assert all(id in [tutor2.id, tutor3.id] for id in resp.json["tutorIds"])

    resp = client.get(
        "/searchtutor",
        query_string={
            "timeRange": json.dumps(
                {
                    "startTime": (datetime.now() + timedelta(hours=1)).isoformat(),
                    "endTime": (
                        datetime.now() + timedelta(days=3, hours=10)
                    ).isoformat(),
                }
            )
        },
    )
    find_many_tutors_mock.assert_called()

    assert resp.status_code == 200
    assert len(resp.json["tutorIds"]) == 1
    assert resp.json["tutorIds"][0] == tutor3.id


def test_search_args(
    setup_test: FlaskClient,
    find_many_tutors_mock: MockType,
    generate_fake_tutors: List[Tutor],
):
    client = setup_test

    tutor1, tutor2, tutor3 = generate_fake_tutors
    find_many_tutors_mock.return_value = [tutor1, tutor2, tutor3]

    # all excluding name
    resp = client.get(
        "/searchtutor",
        query_string={
            "rating": 3,
            "location": "Tasmania",
            "courseOfferings": json.dumps(["science", "math"]),
            "timeRange": json.dumps(
                {
                    "startTime": (datetime.now() + timedelta(hours=1)).isoformat(),
                    "endTime": (
                        datetime.now() + timedelta(days=3, hours=10)
                    ).isoformat(),
                }
            ),
        },
    )
    find_many_tutors_mock.assert_called()

    assert len(resp.json["tutorIds"]) == 1
    assert resp.status_code == 200
    assert resp.json["tutorIds"][0] == tutor3.id
