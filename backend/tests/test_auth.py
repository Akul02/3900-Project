from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType
from flask.testing import FlaskClient
from prisma.models import User


def test_register_not_json(setup_test: FlaskClient):
    client = setup_test
    resp = client.post("/register")
    assert resp.json == {"error": "content-type was not json or data was malformed"}
    assert resp.status_code == 415


def test_register_args(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    fake_student: User,
):
    client = setup_test

    # ensure nothing is actually being created
    mocker.patch("tests.conftest.UserActions.create")

    resp = client.post("/register", json={})
    assert resp.json == {"error": "'name' was missing from field(s)"}
    assert resp.status_code == 400

    resp = client.post("/register", json={"name": "name"})
    assert resp.json == {"error": "'email' was missing from field(s)"}
    assert resp.status_code == 400

    resp = client.post(
        "/register", json={"name": "name", "email": "validemail@mail.com"}
    )
    assert resp.json == {"error": "'password' was missing from field(s)"}
    assert resp.status_code == 400

    resp = client.post(
        "/register",
        json={"name": "name", "email": "validemail@mail.com", "password": "12345678"},
    )
    assert resp.json == {"error": "'accountType' was missing from field(s)"}
    assert resp.status_code == 400

    resp = client.post(
        "/register",
        json={
            "name": "name",
            "email": "validemail@mail.com",
            "password": "12345678",
            "accountType": "notvalid",
        },
    )
    assert resp.json == {"error": "accountType must match student|tutor"}
    assert resp.status_code == 400

    resp = client.post(
        "/register",
        json={
            "name": "name",
            "email": "notvalidemail",
            "password": "12345678",
            "accountType": "student",
        },
    )
    assert resp.json == {"error": "email field is invalid"}
    assert resp.status_code == 400

    resp = client.post(
        "/register",
        json={
            "name": "name",
            "email": "validemail@mail.com",
            "password": "1234567",
            "accountType": "student",
        },
    )
    assert resp.json == {"error": "password field must be at least 8 character(s)"}
    assert resp.status_code == 400

    resp = client.post(
        "/register",
        json={
            "name": "",
            "email": "validemail@mail.com",
            "password": "1234567",
            "accountType": "student",
        },
    )
    assert resp.json == {"error": "name field must be at least 1 character(s)"}
    assert resp.status_code == 400

    find_unique_mock = mocker.patch("tests.conftest.UserActions.find_unique")
    find_unique_mock.return_value = None

    # successfully signup (student)
    resp = client.post(
        "/register",
        json={
            "name": "name",
            "email": "validemail@mail.com",
            "password": "12345678",
            "accountType": "student",
        },
    )
    assert "id" in resp.json
    assert resp.status_code == 200
    with client.session_transaction() as session:
        assert session["user_id"] == resp.json["id"]

    find_unique_mock.assert_called_with(where={"email": fake_student.email})
    find_unique_mock.return_value = fake_student

    resp = client.post(
        "/register",
        json={
            "name": "name",
            "email": "validemail@mail.com",
            "password": "12345678",
            "accountType": "student",
        },
    )
    assert resp.json == {"error": "user already exists with this email"}
    assert resp.status_code == 400

    find_unique_mock.assert_called_with(where={"email": fake_student.email})

    resp = client.post(
        "/register",
        json={
            "name": "name",
            "email": "validemail@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )
    assert resp.json == {"error": "user already exists with this email"}
    assert resp.status_code == 400

    find_unique_mock.assert_called_with(where={"email": fake_student.email})
    find_unique_mock.return_value = None

    # successfully signup (tutor)
    resp = client.post(
        "/register",
        json={
            "name": "name",
            "email": "validemail2@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )
    assert "id" in resp.json
    assert resp.status_code == 200
    with client.session_transaction() as session:
        assert session["user_id"] == resp.json["id"]


################################# LOGIN TESTS ##################################


def test_login_not_json(setup_test: FlaskClient):
    client = setup_test
    resp = client.post("/login")
    assert resp.json == {"error": "content-type was not json or data was malformed"}
    assert resp.status_code == 415


def test_login_args(
    setup_test: FlaskClient,
    find_unique_users_mock: MockType,
    fake_student: User,
):
    client = setup_test
    # Missing email
    resp = client.post("/login", json={})
    assert resp.json == {"error": "'email' was missing from field(s)"}
    assert resp.status_code == 400

    # Missing password
    resp = client.post("/login", json={"email": "validemail@mail.com"})
    assert resp.json == {"error": "'password' was missing from field(s)"}
    assert resp.status_code == 400

    # Missing accountType
    resp = client.post(
        "/login",
        json={"email": "validemail@mail.com", "password": "12345678"},
    )
    assert resp.json == {"error": "'accountType' was missing from field(s)"}
    assert resp.status_code == 400

    # Invalid accountType
    resp = client.post(
        "/login",
        json={
            "email": "validemail@mail.com",
            "password": "12345678",
            "accountType": "notvalid",
        },
    )
    assert resp.json == {"error": "accountType must match student|tutor|admin"}
    assert resp.status_code == 400

    # Invalid password
    resp = client.post(
        "/login",
        json={
            "email": "validemail@mail.com",
            "password": "ab12",
            "accountType": "student",
        },
    )
    assert resp.json == {"error": "password field must be at least 8 character(s)"}
    assert resp.status_code == 400

    # Invalid Email
    resp = client.post(
        "/login",
        json={
            "email": "notvalidemail",
            "password": "12345678",
            "accountType": "student",
        },
    )
    assert resp.json == {"error": "email field is invalid"}
    assert resp.status_code == 400

    # Invalid login attempt (wrong password)
    resp = client.post(
        "/login",
        json={
            "email": "validemail@mail.com",
            "password": "12345677",
            "accountType": "student",
        },
    )
    assert resp.json == {"error": "Invalid login attempt"}
    assert resp.status_code == 401

    # Successful login attempt (student)
    resp = client.post(
        "/login",
        json={
            "email": "validemail@mail.com",
            "password": "12345678",
            "accountType": "student",
        },
    )
    assert resp.status_code == 200
    with client.session_transaction() as session:
        assert session["user_id"] == resp.json["id"]


# Successful login attempt (tutor)
def test_tutor_login(
    setup_test: FlaskClient, find_unique_users_mock: MockType, fake_tutor: User
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
    assert resp.status_code == 200
    with client.session_transaction() as session:
        assert session["user_id"] == resp.json["id"]


# Successful login attempt (admin)
def test_admin_login(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
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
    assert resp.status_code == 200
    with client.session_transaction() as session:
        assert session["user_id"] == resp.json["id"]


def test_login_as_other(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_student: User,
    fake_tutor: User,
    fake_admin: User,
):
    client = setup_test

    resp = client.post(
        "/login",
        json={
            "email": "validemail@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )
    assert resp.json == {"error": "Invalid login attempt"}
    assert resp.status_code == 401

    find_unique_users_mock.assert_called_with(
        where={"email": fake_student.email}, include=mocker.ANY
    )

    resp = client.post(
        "/login",
        json={
            "email": "validemail@mail.com",
            "password": "12345678",
            "accountType": "admin",
        },
    )
    assert resp.json == {"error": "Invalid login attempt"}
    assert resp.status_code == 401

    find_unique_users_mock.assert_called_with(
        where={"email": fake_student.email}, include=mocker.ANY
    )

    resp = client.post(
        "/login",
        json={
            "email": "validemail2@mail.com",
            "password": "12345678",
            "accountType": "student",
        },
    )
    assert resp.json == {"error": "Invalid login attempt"}
    assert resp.status_code == 401

    find_unique_users_mock.assert_called_with(
        where={"email": fake_tutor.email}, include=mocker.ANY
    )

    resp = client.post(
        "/login",
        json={
            "email": "validemail2@mail.com",
            "password": "12345678",
            "accountType": "admin",
        },
    )
    assert resp.json == {"error": "Invalid login attempt"}
    assert resp.status_code == 401

    find_unique_users_mock.assert_called_with(
        where={"email": fake_tutor.email}, include=mocker.ANY
    )

    resp = client.post(
        "/login",
        json={
            "email": "validemail3@mail.com",
            "password": "12345678",
            "accountType": "student",
        },
    )
    assert resp.json == {"error": "Invalid login attempt"}
    assert resp.status_code == 401

    find_unique_users_mock.assert_called_with(
        where={"email": fake_admin.email}, include=mocker.ANY
    )

    resp = client.post(
        "/login",
        json={
            "email": "validemail3@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )
    assert resp.json == {"error": "Invalid login attempt"}
    assert resp.status_code == 401

    find_unique_users_mock.assert_called_with(
        where={"email": fake_admin.email}, include=mocker.ANY
    )


################################# LOGOUT TESTS #################################


def test_logout_no_user(setup_test: FlaskClient):
    client = setup_test
    with client.session_transaction() as session:
        assert ("user_id" not in session) == True
    resp = client.post("/logout")
    assert resp.json == {"success": True}
    assert resp.status_code == 200


def test_logout_student(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_student: User,
):
    client = setup_test

    resp1 = client.post(
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

    with client.session_transaction() as session:
        assert session["user_id"] == resp1.json["id"]

    resp2 = client.post("/logout")
    with client.session_transaction() as session:
        assert ("user_id" not in session) == True
    assert resp2.status_code == 200
    assert resp2.json["success"] == True


def test_logout_tutor(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_tutor: User,
):
    client = setup_test

    resp1 = client.post(
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

    with client.session_transaction() as session:
        assert session["user_id"] == resp1.json["id"]

    resp = client.post("/logout", json={})
    with client.session_transaction() as session:
        assert ("user_id" not in session) == True
    assert resp.status_code == 200
    assert resp.json["success"] == True


def test_logout_admin(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_admin: User,
):
    client = setup_test

    resp1 = client.post(
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

    with client.session_transaction() as session:
        assert session["user_id"] == resp1.json["id"]

    resp = client.post("/logout", json={})
    with client.session_transaction() as session:
        assert ("user_id" not in session) == True
    assert resp.status_code == 200
    assert resp.json["success"] == True


########################## RESET PASSWORD TESTS ################################


# Not correct json input
def test_resetpassword_not_json(setup_test: FlaskClient):
    client = setup_test
    resp = client.put("/resetpassword")
    assert resp.json == {"error": "content-type was not json or data was malformed"}
    assert resp.status_code == 415


# No user logged in
def test_resetpassword_no_user(setup_test: FlaskClient, fake_student):
    client = setup_test
    with client.session_transaction() as session:
        assert ("user_id" not in session) == True
    resp = client.put(
        "/resetpassword", json={"id": fake_student.id, "newPassword": "123456789"}
    )
    assert resp.status_code == 401
    assert resp.json == {"error": "No user is logged in"}


# Student logged in
def test_resetpassword_student_login(
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

    resp = client.put(
        "/resetpassword", json={"id": fake_student.id, "newPassword": "123456789"}
    )
    assert resp.json == {"error": "Insufficient permission to modify this profile"}
    assert resp.status_code == 403


# Tutor logged in
def test_resetpassword_tutor_login(
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

    resp = client.put(
        "/resetpassword", json={"id": fake_tutor.id, "newPassword": "123456789"}
    )
    assert resp.json == {"error": "Insufficient permission to modify this profile"}
    assert resp.status_code == 403


# Admin logged in Reset Password Tests
def test_resetpassword_student(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_student: User,
    fake_admin: User,
    fake_user: User,
):
    client = setup_test

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

    # Missing id
    resp = client.put("/resetpassword", json={})
    assert resp.json == {"error": "'id' was missing from field(s)"}
    assert resp.status_code == 400

    # Missing newPassword
    resp = client.put("/resetpassword", json={"id": fake_student.id})
    assert resp.json == {"error": "'newPassword' was missing from field(s)"}
    assert resp.status_code == 400

    # Invalid newPassword
    resp = client.put(
        "/resetpassword", json={"id": fake_student.id, "newPassword": "1234567"}
    )
    assert resp.json == {"error": "newPassword field must be at least 8 character(s)"}
    assert resp.status_code == 400

    # Invalid id
    resp = client.put(
        "/resetpassword", json={"id": "notvalid", "newPassword": "123456789"}
    )
    assert resp.json == {"error": "Profile does not exist"}
    assert resp.status_code == 404

    # New password cannot be the same as the old password
    resp = client.put(
        "/resetpassword", json={"id": fake_student.id, "newPassword": "12345678"}
    )
    assert resp.json == {"error": "New password cannot be the same as the old password"}
    assert resp.status_code == 400
    find_unique_users_mock.assert_called_with(where={"id": fake_student.id})

    update_mock = mocker.patch("tests.conftest.UserActions.update")

    # Successful reset password
    resp = client.put(
        "/resetpassword",
        json={"id": fake_student.id, "newPassword": "123456789"},
    )

    find_unique_users_mock.assert_called_with(where={"id": fake_student.id})
    update_mock.assert_called()

    assert resp.json == {"success": True}
    assert resp.status_code == 200

    # Test login with new password
    client.post("/logout", json={})

    mocker.stop(find_unique_users_mock)
    find_unique_users_mock = mocker.patch("tests.conftest.UserActions.find_unique")
    find_unique_users_mock.return_value = fake_user(
        fake_student.email, "123456789", "student"
    )

    resp = client.post(
        "/login",
        json={
            "email": "validemail@mail.com",
            "password": "12345678",
            "accountType": "student",
        },
    )
    assert resp.json == {"error": "Invalid login attempt"}

    find_unique_users_mock.assert_called_with(
        where={"email": fake_student.email}, include=mocker.ANY
    )

    resp = client.post(
        "/login",
        json={
            "email": "validemail@mail.com",
            "password": "123456789",
            "accountType": "student",
        },
    )

    find_unique_users_mock.assert_called_with(
        where={"email": fake_student.email}, include=mocker.ANY
    )

    assert resp.status_code == 200
    with client.session_transaction() as session:
        assert session["user_id"] == resp.json["id"]


# Admin logged in Tutor Reset Password Tests
def test_resetpassword_tutor(
    setup_test: FlaskClient,
    mocker: MockerFixture,
    find_unique_users_mock: MockType,
    fake_admin: User,
    fake_tutor: User,
    fake_user: User,
):
    client = setup_test

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

    # Missing newPassword
    resp = client.put("/resetpassword", json={"id": fake_tutor.id})
    assert resp.json == {"error": "'newPassword' was missing from field(s)"}
    assert resp.status_code == 400

    # Invalid newPassword
    resp = client.put(
        "/resetpassword", json={"id": fake_tutor.id, "newPassword": "1234567"}
    )
    assert resp.json == {"error": "newPassword field must be at least 8 character(s)"}
    assert resp.status_code == 400

    # New password cannot be the same as the old password
    resp = client.put(
        "/resetpassword", json={"id": fake_tutor.id, "newPassword": "12345678"}
    )
    assert resp.json == {"error": "New password cannot be the same as the old password"}
    assert resp.status_code == 400
    find_unique_users_mock.assert_called_with(where={"id": fake_tutor.id})

    update_mock = mocker.patch("tests.conftest.UserActions.update")
    # Successful reset password
    resp = client.put(
        "/resetpassword",
        json={"id": fake_tutor.id, "newPassword": "123456789"},
    )
    assert resp.json == {"success": True}
    assert resp.status_code == 200

    find_unique_users_mock.assert_called_with(where={"id": fake_tutor.id})
    update_mock.assert_called()

    mocker.stop(find_unique_users_mock)
    find_unique_users_mock = mocker.patch("tests.conftest.UserActions.find_unique")
    find_unique_users_mock.return_value = fake_user(
        fake_tutor.email, "123456789", "tutor"
    )

    # Test login with new password
    client.post("/logout", json={})
    resp = client.post(
        "/login",
        json={
            "email": "validemail2@mail.com",
            "password": "12345678",
            "accountType": "tutor",
        },
    )
    assert resp.json == {"error": "Invalid login attempt"}

    find_unique_users_mock.assert_called_with(
        where={"email": fake_tutor.email}, include=mocker.ANY
    )

    resp = client.post(
        "/login",
        json={
            "email": "validemail2@mail.com",
            "password": "123456789",
            "accountType": "tutor",
        },
    )
    assert resp.status_code == 200
    with client.session_transaction() as session:
        assert session["user_id"] == resp.json["id"]

    find_unique_users_mock.assert_called_with(
        where={"email": fake_tutor.email}, include=mocker.ANY
    )
