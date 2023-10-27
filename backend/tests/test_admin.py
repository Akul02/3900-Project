from flask.testing import FlaskClient
from prisma.models import User
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType


def test_admin_search_not_login(setup_test: FlaskClient):
    client = setup_test

    resp = client.get("/admin/search")
    assert resp.status_code == 401
    assert resp.json["error"] == "No user is logged in"


def test_admin_search_student_login(
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

    resp = client.get("/admin/search")
    assert resp.status_code == 403
    assert resp.json["error"] == "Insufficient permission to search for users"


def test_admin_search_tutor_login(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
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

    resp = client.get("/admin/search")
    assert resp.status_code == 403
    assert resp.json["error"] == "Insufficient permission to search for users"


def test_admin_search_no_args(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    find_many_users_mock: MockType,
    fake_student,
    fake_tutor,
    fake_admin,
):
    client = setup_test

    # login as admin
    client.post(
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

    find_many_users_mock.return_value = [fake_student, fake_tutor, fake_admin]

    resp = client.get("/admin/search")
    find_many_users_mock.assert_called()

    assert resp.status_code == 200
    assert all(
        id in [fake_student.id, fake_tutor.id, fake_admin.id]
        for id in resp.json["userIds"]
    )


def test_admin_search_id(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    find_many_users_mock: MockType,
    fake_student,
    fake_tutor,
    fake_admin,
):
    client = setup_test

    # login as admin
    client.post(
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

    # id belongs to no one
    find_many_users_mock.return_value = []

    resp = client.get("/admin/search", query_string={"id": "nonexist"})
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert len(resp.json["userIds"]) == 0

    # student
    find_many_users_mock.return_value = [fake_student]

    resp = client.get("/admin/search", query_string={"id": fake_student.id})
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_student.id]

    # tutor
    find_many_users_mock.return_value = [fake_tutor]

    resp = client.get("/admin/search", query_string={"id": fake_tutor.id})
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_tutor.id]

    # admin
    find_many_users_mock.return_value = [fake_admin]

    resp = client.get("/admin/search", query_string={"id": fake_admin.id})
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_admin.id]


def test_admin_search_name(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    find_many_users_mock: MockType,
    fake_student,
    fake_tutor,
    fake_admin,
):
    client = setup_test

    # login as admin
    client.post(
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

    # invalid name
    resp = client.get("/admin/search", query_string={"name": ""})

    assert resp.status_code == 400
    assert resp.json["error"] == "name field must be at least 1 character(s)"

    # name belongs to no one
    find_many_users_mock.return_value = []

    resp = client.get("/admin/search", query_string={"name": "nonexist"})
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert len(resp.json["userIds"]) == 0

    # student
    find_many_users_mock.return_value = [fake_student]

    resp = client.get("/admin/search", query_string={"name": fake_student.name})
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_student.id]

    # tutor
    find_many_users_mock.return_value = [fake_tutor]

    resp = client.get("/admin/search", query_string={"name": fake_tutor.name})
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_tutor.id]

    # admin
    find_many_users_mock.return_value = [fake_admin]

    resp = client.get("/admin/search", query_string={"name": fake_admin.name})
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_admin.id]


def test_admin_search_email(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    find_many_users_mock: MockType,
    fake_student,
    fake_tutor,
    fake_admin,
):
    client = setup_test

    # login as admin
    client.post(
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

    # invalid email
    resp = client.get("/admin/search", query_string={"email": "invalidmail"})

    assert resp.status_code == 400
    assert resp.json["error"] == "email field is invalid"

    # email belongs to no one
    find_many_users_mock.return_value = []

    resp = client.get("/admin/search", query_string={"email": "nonexist@mail.com"})
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert len(resp.json["userIds"]) == 0

    # student
    find_many_users_mock.return_value = [fake_student]

    resp = client.get("/admin/search", query_string={"email": fake_student.email})
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_student.id]

    # tutor
    find_many_users_mock.return_value = [fake_tutor]

    resp = client.get("/admin/search", query_string={"email": fake_tutor.email})
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_tutor.id]

    # admin
    find_many_users_mock.return_value = [fake_admin]

    resp = client.get("/admin/search", query_string={"email": fake_admin.email})
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_admin.id]


def test_admin_search_phone_number(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    find_many_users_mock: MockType,
    fake_student,
    fake_tutor,
    fake_admin,
):
    client = setup_test

    # login as admin
    client.post(
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

    # phone number belongs to no one
    find_many_users_mock.return_value = []

    resp = client.get("/admin/search", query_string={"phoneNumber": "0400000000"})
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert len(resp.json["userIds"]) == 0

    # student
    find_many_users_mock.return_value = [fake_student]

    resp = client.get(
        "/admin/search", query_string={"phoneNumber": fake_student.phoneNumber}
    )
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_student.id]

    # tutor
    find_many_users_mock.return_value = [fake_tutor]

    resp = client.get(
        "/admin/search", query_string={"phoneNumber": fake_tutor.phoneNumber}
    )
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_tutor.id]

    # admin
    find_many_users_mock.return_value = [fake_admin]

    resp = client.get(
        "/admin/search", query_string={"phoneNumber": fake_admin.phoneNumber}
    )
    find_many_users_mock.assert_called_once()
    find_many_users_mock.reset_mock()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_admin.id]


def test_admin_search_account_type(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    find_many_tutors_mock: MockType,
    find_many_students_mock: MockType,
    find_many_admins_mock: MockType,
    fake_student,
    fake_tutor,
    fake_admin,
):
    client = setup_test

    # login as admin
    client.post(
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

    # invalid account type
    resp = client.get("/admin/search", query_string={"accountType": "invalid"})

    assert resp.status_code == 400
    assert resp.json["error"] == "accountType must match student|tutor|admin"

    # student
    find_many_students_mock.return_value = [fake_student.studentInfo]

    resp = client.get("/admin/search", query_string={"accountType": "student"})
    find_many_students_mock.assert_called_once()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_student.id]

    # tutor
    find_many_tutors_mock.return_value = [fake_tutor.tutorInfo]

    resp = client.get("/admin/search", query_string={"accountType": "tutor"})
    find_many_tutors_mock.assert_called_once()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_tutor.id]

    # admin
    find_many_admins_mock.return_value = [fake_admin.adminInfo]

    resp = client.get("/admin/search", query_string={"accountType": "admin"})
    find_many_admins_mock.assert_called_once()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_admin.id]


def test_admin_search_args(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    find_many_students_mock: MockType,
    fake_student,
    fake_admin,
):
    client = setup_test

    # login as admin
    client.post(
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

    # excluding id given it's a unique attribute
    find_many_students_mock.return_value = [fake_student.studentInfo]

    resp = client.get(
        "/admin/search",
        query_string={
            "name": fake_student.name,
            "email": fake_student.email,
            "phoneNumber": fake_student.phoneNumber,
            "accountType": "student",
        },
    )
    find_many_students_mock.assert_called_once()

    assert resp.status_code == 200
    assert resp.json["userIds"] == [fake_student.id]


def test_admin_create_not_login(setup_test: FlaskClient):
    client = setup_test

    resp = client.post(
        "admin/create",
        json={
            "name": "newAdmin",
            "email": "email@email.com",
            "password": "12345678",
        },
    )
    assert resp.status_code == 401
    assert resp.json["error"] == "No user is logged in"


def test_admin_create_student_login(
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

    resp = client.post(
        "admin/create",
        json={
            "name": "newAdmin",
            "email": "email@email.com",
            "password": "12345678",
        },
    )
    assert resp.status_code == 403
    assert resp.json["error"] == "Insufficient permission to create a new admin account"


def test_admin_create_tutor_login(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
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

    resp = client.post(
        "admin/create",
        json={
            "name": "newAdmin",
            "email": "email@email.com",
            "password": "12345678",
        },
    )
    assert resp.status_code == 403
    assert resp.json["error"] == "Insufficient permission to create a new admin account"


def test_admin_create_invalid_args(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_admin,
):
    client = setup_test

    # login as admin
    client.post(
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
    # omitted name
    resp = client.post(
        "admin/create",
        json={
            "email": "email@email.com",
            "password": "12345678",
        },
    )
    assert resp.status_code == 400
    assert resp.json["error"] == "'name' was missing from field(s)"

    # omitted email
    resp = client.post(
        "admin/create",
        json={
            "name": "newAdmin",
            "password": "12345678",
        },
    )
    assert resp.status_code == 400
    assert resp.json["error"] == "'email' was missing from field(s)"

    # omitted password
    resp = client.post(
        "admin/create",
        json={
            "name": "newAdmin",
            "email": "email@email.com",
        },
    )
    assert resp.status_code == 400
    assert resp.json["error"] == "'password' was missing from field(s)"

    # invalid email
    resp = client.post(
        "admin/create",
        json={
            "name": "newAdmin",
            "email": "notvalid",
            "password": "12345678",
        },
    )
    assert resp.status_code == 400
    assert resp.json["error"] == "email field is invalid"

    # invalid name
    resp = client.post(
        "admin/create",
        json={
            "name": "",
            "email": "mail@gmail.com",
            "password": "12345678",
        },
    )
    assert resp.status_code == 400
    assert resp.json["error"] == "name field must be at least 1 character(s)"

    # invalid password
    resp = client.post(
        "admin/create",
        json={
            "name": "newAdmin",
            "email": "mail@gmail.com",
            "password": "1234567",
        },
    )
    assert resp.status_code == 400
    assert resp.json["error"] == "password field must be at least 8 character(s)"


def test_create_admin_valid(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    find_many_admins_mock: MockType,
    fake_admin,
    fake_user,
):
    client = setup_test

    # login as admin
    client.post(
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

    user_create_mock = mocker.patch("tests.conftest.UserActions.create")
    resp = client.post(
        "admin/create",
        json={
            "name": "newAdmin",
            "email": "email@email.com",
            "password": "12345678",
        },
    )
    user_create_mock.assert_called()
    assert resp.status_code == 200

    # go 'find' new admin
    new_fake_admin: User = fake_user("email@email.com", "12345678", "admin")
    new_fake_admin.name = "newAdmin"
    new_fake_admin.id = resp.json["id"]

    find_many_admins_mock.return_value = [
        fake_admin.adminInfo,
        new_fake_admin.adminInfo,
    ]

    resp = client.get("/admin/search", query_string={"accountType": "admin"})
    find_many_admins_mock.assert_called_once()

    assert resp.status_code == 200
    assert all(id in [new_fake_admin.id, fake_admin.id] for id in resp.json["userIds"])
