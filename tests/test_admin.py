import os
import pytest
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed
import sys

sys.path.append(os.getcwd())

from app.auth.admin import MyAuthProvider

@pytest.fixture
def auth_provider():
    return MyAuthProvider()


@pytest.fixture
def my_request():
    scope = {
        'type': 'http',
        'asgi': {'version': '3.0'},
        'http_version': '1.1',
        'method': 'GET',
        'path': '/',
        'root_path': '',
        'scheme': 'http',
        'query_string': b'',
        'headers': [],
    }
    return Request(scope)


@pytest.fixture
def response():
    return Response()


@pytest.mark.asyncio
async def test_login_success(auth_provider, my_request, response):
    username = "admin"
    password = "password"
    remember_me = True

    result = await auth_provider.login(username, password, remember_me, my_request, response)

    assert result == response
    assert my_request.session.get("username") == username


@pytest.mark.asyncio
async def test_login_invalid_username(auth_provider, my_request, response):
    username = "a"
    password = "password"
    remember_me = True

    with pytest.raises(FormValidationError) as exc_info:
        await auth_provider.login(username, password, remember_me, my_request, response)

    assert str(exc_info.value) == "Ensure username has at least 03 characters"


@pytest.mark.asyncio
async def test_login_invalid_credentials(auth_provider, my_request, response):
    username = "admin"
    password = "wrong_password"
    remember_me = True

    with pytest.raises(LoginFailed) as exc_info:
        await auth_provider.login(username, password, remember_me, my_request, response)

    assert str(exc_info.value) == "Invalid username or password"


@pytest.mark.asyncio
async def test_is_authenticated_authenticated(auth_provider, my_request):
    my_request.session["username"] = "admin"

    result = await auth_provider.is_authenticated(my_request)

    assert result is True
    assert my_request.state.user == AdminUser(username="admin")


@pytest.mark.asyncio
async def test_is_authenticated_not_authenticated(auth_provider, my_request):
    my_request.session.clear()

    result = await auth_provider.is_authenticated(my_request)

    assert result is False


@pytest.mark.asyncio
async def test_logout(auth_provider, my_request, response):
    my_request.session["username"] = "admin"

    result = await auth_provider.logout(my_request, response)

    assert result == response
    assert my_request.session.get("username") is None