from dataclasses import dataclass
from typing import Optional

from fastapi.exceptions import HTTPException
from sqlalchemy.exc import OperationalError

from app.common.config import MAX_API_KEY, MAX_API_WHITELIST


def error_codes(status_code: int, internal_code: int) -> str:
    return f"{status_code}{str(internal_code).zfill(4)}"


class APIException(Exception):
    status_code: int = 500
    internal_code: int = 0
    msg: Optional[str]
    detail: Optional[str]
    ex: Optional[Exception]

    def __init__(
        self,
        *,
        status_code: int,
        internal_code: int,
        msg: Optional[str] = None,
        detail: Optional[str] = None,
        ex: Optional[Exception] = None,
    ):
        self.status_code = status_code
        self.code = error_codes(
            status_code=status_code, internal_code=internal_code
        )
        self.msg = msg
        self.detail = detail
        self.ex = ex
        super().__init__(ex)

    def __call__(
        self,
        lazy_format: Optional[dict[str, str]] = None,
        ex: Optional[Exception] = None,
    ) -> "APIException":
        if (
            self.msg is not None
            and self.detail is not None
            and lazy_format is not None
        ):  # lazy format for msg and detail
            self.msg = self.msg.format(**lazy_format)
            self.detail = self.detail.format(**lazy_format)
        if ex is not None:  # set exception if exists
            self.ex = ex
        return self


class InternalServerError(APIException):
    status_code: int = 500
    internal_code: int = 9999
    msg: str = "This is a server-side error. It will be automatically reported and fixed as soon as possible."
    detail: str = "Internal Server Error"

    def __init__(self, ex: Optional[Exception] = None):
        super().__init__(
            status_code=self.status_code,
            internal_code=self.internal_code,
            msg=self.msg,
            detail=self.detail,
            ex=ex,
        )


class InvalidIpError(APIException):
    status_code: int = 400
    internal_code: int = 10
    msg: str = "{ip} is invalid."
    detail: str = "invalid IP : {ip}"

    def __init__(self, ip: str):
        super().__init__(
            status_code=400,
            internal_code=self.internal_code,
            msg=self.msg.format(ip=ip),
            detail=self.detail.format(ip=ip),
        )


@dataclass(frozen=True)
class Responses_400:
    """
    The client is making a request in the wrong way
    """

    no_email_or_password: APIException = APIException(
        status_code=400,
        internal_code=1,
        msg="Please enter both email and password.",
        detail="Email and PW must be provided.",
    )
    email_already_exists: APIException = APIException(
        status_code=400,
        internal_code=2,
        msg="The email is already registered.",
        detail="Email already exists.",
    )
    not_supported_feature: APIException = APIException(
        status_code=400,
        internal_code=3,
        msg="This feature is not available yet.",
        detail="Not supported feature.",
    )
    unregister_failure: APIException = APIException(
        status_code=400,
        internal_code=4,
        msg="Failed to unregister.",
        detail="Failed to unregister.",
    )
    max_key_count_exceed: APIException = APIException(
        status_code=400,
        internal_code=8,
        msg=f"API key creation is possible up to {MAX_API_KEY}.",
        detail="Max Key Count Reached",
    )
    max_whitekey_count_exceed: APIException = APIException(
        status_code=400,
        internal_code=9,
        msg=f"Whitelist creation is possible up to {MAX_API_WHITELIST}.",
        detail="Max Whitelist Count Reached",
    )
    invalid_ip: APIException = APIException(
        status_code=400,
        internal_code=10,
        msg="{ip} is not a valid IP.",
        detail="invalid IP : {ip}",
    )
    invalid_api_query: APIException = APIException(
        status_code=400,
        internal_code=11,
        msg="Query string only allows 2 keys, and both must be submitted when requested.",
        detail="Query String Only Accept key and timestamp.",
    )
    kakao_send_failure: APIException = APIException(
        status_code=400,
        internal_code=15,
        msg="Failed to send KAKAO MSG.",
        detail="Failed to send KAKAO MSG.",
    )
    websocket_in_use: APIException = APIException(
        status_code=400,
        internal_code=16,
        msg="The websocket is already in use.",
        detail="Websocket is already in use.",
    )
    invalid_email_format: APIException = APIException(
        status_code=400,
        internal_code=17,
        msg="Invalid email format.",
        detail="Invalid Email Format.",
    )
    email_length_not_in_range: APIException = APIException(
        status_code=400,
        internal_code=18,
        msg="Please enter an email of 6 to 50 characters.",
        detail="Email must be 6 ~ 50 characters.",
    )
    password_length_not_in_range: APIException = APIException(
        status_code=400,
        internal_code=19,
        msg="Please enter a password of 6 to 100 characters.",
        detail="Password must be 6 ~ 100 characters.",
    )

@dataclass(frozen=True)
class Responses_401:
    """
    The client must present correct credentials (security related)
    """

    not_authorized: APIException = APIException(
        status_code=401,
        internal_code=1,
        msg="This service requires login.",
        detail="Authorization Required",
    )
    token_expired: APIException = APIException(
        status_code=401,
        internal_code=6,
        msg="Your session has expired and you have been logged out.",
        detail="Token Expired",
    )
    token_decode_failure: APIException = APIException(
        status_code=401,
        internal_code=7,
        msg="This is an abnormal access.",
        detail="Token has been compromised.",
    )
    invalid_api_header: APIException = APIException(
        status_code=401,
        internal_code=12,
        msg="There is no hashed Secret in the header, or it is invalid.",
        detail="Invalid HMAC secret in Header",
    )
    invalid_timestamp: APIException = APIException(
        status_code=401,
        internal_code=13,
        msg="The timestamp included in the query string must be in KST, must be less than the current time, and must be greater than the current time - 10 seconds.",
        detail="timestamp in Query String must be KST, Timestamp must be less than now, and greater than now - 10.",
    )

@dataclass(frozen=True)
class Responses_404:
    """
    The client requested something, but nothing could be found for the item
    """

    not_found_user: APIException = APIException(
        status_code=404,
        internal_code=5,
        msg="The user could not be found.",
        detail="Not found user.",
    )
    not_found_access_key: APIException = APIException(
        status_code=404,
        internal_code=14,
        msg="Could not find an API key that matches the Access key.",
        detail="Not found such API Access Key",
    )
    not_found_api_key: APIException = APIException(
        status_code=404,
        internal_code=7,
        msg="Could not find an Api key that matches the provided conditions.",
        detail="No API Key matched such conditions",
    )
    not_found_preset: APIException = APIException(
        status_code=404,
        internal_code=13,
        msg="Could not find a preset that matches the provided conditions.",
        detail="No preset matched such conditions",
    )

@dataclass(frozen=True)
class Responses_500:
    """
    An error occurred internally on the server
    """

    middleware_exception: APIException = APIException(
        status_code=500,
        internal_code=2,
        detail="Middleware could not be initialized",
    )
    websocket_error: APIException = APIException(
        status_code=500,
        internal_code=3,
        msg="Problem with websocket connection",
        detail="Websocket error",
    )
    database_not_initialized: APIException = APIException(
        status_code=500,
        internal_code=4,
        msg="The database has not been initialized.",
        detail="Database not initialized",
    )
    cache_not_initialized: APIException = APIException(
        status_code=500,
        internal_code=5,
        msg="The cache has not been initialized.",
        detail="Cache not initialized",
    )
    vectorestore_not_initialized: APIException = APIException(
        status_code=500,
        internal_code=5,
        msg="The vector store has not been initialized.",
        detail="Vector Store not initialized",
    )


def exception_handler(
    error: Exception,
) -> InternalServerError | HTTPException | APIException:
    if isinstance(error, APIException):
        if error.status_code == 500:
            return InternalServerError(ex=error)
        else:
            return error
    elif isinstance(error, OperationalError):
        return InternalServerError(ex=error)
    elif isinstance(error, HTTPException):
        return error
    else:
        return InternalServerError()
