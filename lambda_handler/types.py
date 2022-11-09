"""Type stubs and protocols"""

from lambda_handler.model import AwsEvent, LambdaResponse

from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    MutableMapping,
    Optional,
    Type,
    TypeVar,
)
from typing_extensions import Protocol, TypeAlias, TypedDict

#: pylint: disable=invalid-name, too-few-public-methods
AwsEventType = TypeVar("AwsEventType", bound=AwsEvent)


AwsEventTypedCallable = Callable[[AwsEventType], LambdaResponse]
AwsEventCallable = Callable[[Dict[str, Any]], LambdaResponse]

AwsEventRawCallable = Callable[[Dict[str, Any]], Dict[str, Any]]


class LambdaHandlerInterface(Protocol):
    """Class with an `add_event_func` method"""

    def add_event_func(
        self,
        event_type: Type[AwsEvent],
        event_key: str,
        func: Callable[[Dict[str, Any]], Dict[str, Any]],
    ):
        """Add an event function to the instance"""
        pass


LambdaEvent = Dict[str, Any]

Headers: TypeAlias = List[List[bytes]]


class Response(TypedDict):
    """Response typed dictionary"""

    status: int
    headers: Headers
    body: bytes


class LambdaCognitoIdentity(Protocol):
    """Lambda cognito identity"""

    cognito_identity_id: str
    cognito_identity_pool_id: str


class LambdaMobileClient(Protocol):
    "Lambda mobile client"

    installation_id: str
    app_title: str
    app_version_name: str
    app_version_code: str
    app_package_name: str


class LambdaMobileClientContext(Protocol):
    """Lambda mobile client context"""

    client: LambdaMobileClient
    custom: Dict[str, Any]
    env: Dict[str, Any]


class LambdaContext(Protocol):
    """Lambda context"""

    function_name: str
    function_version: str
    invoked_function_arn: str
    memory_limit_in_mb: int
    aws_request_id: str
    log_group_name: str
    log_stream_name: str
    identity: Optional[LambdaCognitoIdentity]
    client_context: Optional[LambdaMobileClientContext]

    def get_remaining_time_in_millis(self) -> int:
        """Returns the number of milliseconds left before the execution times out."""
        pass


Message: TypeAlias = MutableMapping[str, Any]
Scope: TypeAlias = MutableMapping[str, Any]
Receive: TypeAlias = Callable[[], Awaitable[Message]]
Send: TypeAlias = Callable[[Message], Awaitable[None]]


class FastApiInterface(Protocol):
    """FastAPI protocol"""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        ...  # pragma: no cover


class MangumInterface(Protocol):
    """Callable protocol"""

    def __call__(self, event: LambdaEvent, context: LambdaContext) -> dict:
        pass
