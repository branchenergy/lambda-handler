"""Defines the main `LambdaHandler` class"""

import re

from lambda_handler.model import (
    ApiGatewayEvent,
    AwsEvent,
    DirectInvocationEvent,
    EventBridgeEvent,
    S3Event,
    SnsEvent,
    SqsEvent,
)
from lambda_handler.types import (
    AwsEventRawCallable,
    FastApiInterface,
    LambdaContext,
    LambdaHandlerInterface,
    MangumInterface,
)
from lambda_handler.utils import (
    OnetimeDictionary,
    DictCallable,
    TypedCallable,
    _P,
    create_wrapper,
    parse_lambda_event,
)

from typing import (
    Any,
    Callable,
    Dict,
    Literal,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
    overload,
)
from typing_extensions import TypeAlias

__all__ = ["InvalidRouteError", "ExistingRouteError", "LambdaHandler"]


Bool: TypeAlias = Union[Literal[True], Literal[False]]


VALID_EVENTS = [
    "DirectInvocationEvent",
    "EventBridgeEvent",
    "S3Event",
    "SqsEvent",
    "SnsEvent",
]


class InvalidRouteError(Exception):
    """Raised when a route is not registered with the handler"""

    pass


class ExistingRouteError(Exception):
    """Raised when an existing route is overwritten by another handling
    function
    """

    pass


class NoFastAPIInstanceError(Exception):
    """Raised when an AWS API Gateway Proxy event is passed to a handler
    without a FastAPI instance
    """

    pass


class LambdaHandler(LambdaHandlerInterface):
    """AWS AWS Lambda Handler

    This class is the top-level handler which provides wrappers for module functions
    which handle AWS Lambda events of different types.

    Parameters
    ----------
    fastapi_app : Optional[FastApiInterface] = None
        Optional FastAPI instance for handling HTTP requests

    Examples
    --------
    ```python
    from lambda_handler import LambdaHandler, SnsEvent, LambdaResponse

    handler = LambdaHandler()

    @handler.sns(topic_name="MyTopic")
    def handle_mytopic(event: SnsEvent) -> LambdaResponse:
        body = frobincate()
        return LambdaResponse(status_code=200, body=body)
    ```
    """

    def __init__(self, fastapi_app: Optional[FastApiInterface] = None):
        self._events_dict: Dict[Tuple[str, str], AwsEventRawCallable] = (
            OnetimeDictionary()
        )
        self._fastapi_app: Optional[FastApiInterface] = None
        self._mangum: Optional[MangumInterface] = None

        if fastapi_app is not None:
            try:
                #: pylint: disable=import-outside-toplevel
                from fastapi import FastAPI
                from mangum import Mangum

                #: pylint: enable=import-outside-toplevel
            except ImportError:
                raise ImportError(
                    "Cannot import FastAPI and Mangum! Are these installed?"
                ) from None  #: noqa

            cast(FastAPI, fastapi_app)
            self._fastapi_app = fastapi_app
            self._mangum = Mangum(fastapi_app)

    def __call__(self, event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
        return self.process_event(event, context)

    @property
    def fastapi_app(self) -> Optional[FastApiInterface]:
        """FastAPI app instance, if there is one

        Returns
        -------
        Optional[FastAPI]
            FastAPI app instance, if there is one
        """
        return self._fastapi_app

    @fastapi_app.setter
    def fastapi_app(self, fastapi_app: FastApiInterface) -> None:
        try:
            #: pylint: disable=import-outside-toplevel
            from fastapi import FastAPI
            from mangum import Mangum

            #: pylint: enable=import-outside-toplevel
        except ImportError:
            raise ImportError(
                "Cannot import FastAPI and Mangum! Are these installed?"
            ) from None
        if not isinstance(fastapi_app, FastAPI):
            raise ValueError("`fastapi_app` must be a `FastAPI` instance!")
        self._fastapi_app = fastapi_app
        self._mangum = Mangum(fastapi_app)

    @property
    def mangum(self) -> Optional[MangumInterface]:
        """Mangum handler instance, if there is one

        Returns
        -------
        Optional[MangumInterface]
            Mangum app instance, if there is one
        """
        return self._mangum

    def _find_function(
        self, event_type_name: str, event_key: str
    ) -> AwsEventRawCallable:
        """Find the handling function for the given event type and key

        Parameters
        ----------
        event_type_name : str
            Name of the event class
        event_key : str
            Event key

        Returns
        -------
        AwsEventRawCallable
            Event handling function

        Raises
        ------
        InvalidRouteError
            If no handling function is found
        """

        for (event_type, key), func in self._events_dict.items():
            if event_type == event_type_name:
                if re.match(key, event_key):
                    return func

        raise InvalidRouteError(
            f"No valid route for event type `{event_type_name}` and event key"
            f" `{event_key}`"
        )

    def process_event(
        self, event: Dict[str, Any], context: LambdaContext
    ) -> Dict[str, Any]:
        """Process an event into an `AwsEvent` instance and pass it to its
        handling function

        Parameters
        ----------
        event : Dict[str, Any]
            Event dictionary
        context : LambdaContext
            Lambda context object

        Returns
        -------
        Dict[str, Any]
            Response dictionary

        Raises
        ------
        InvalidRouteError
            Raised when there is no valid route for the event
        """
        parsed_event = parse_lambda_event(event)

        if not isinstance(parsed_event, ApiGatewayEvent):
            event_type_name = type(parsed_event).__qualname__.split("[")[0]

            func = self._find_function(event_type_name, parsed_event.event_key)

            # The function itself parses the event so we don't need to
            # pass the parsed event

            return func(event)

        if self.mangum is None:
            raise NoFastAPIInstanceError("No FastAPI instance set on handler!")

        #: pylint: disable=not-callable
        return self.mangum(parsed_event.__root__, context)

    def add_event_func(
        self,
        event_type: Type[AwsEvent],
        event_key: str,
        func: AwsEventRawCallable,
    ) -> None:
        """Register an event function on the instance

        Parameters
        ----------
        event_type: AwsEventType
            The type of event
        event_key: str
            The event key (topic name, queue name, etc)
        func: Union[AwsEventTypedCallable[AwsEvent], AwsEventRawCallable]
            The callable to register the event for
        """
        if event_type.__qualname__ not in VALID_EVENTS:
            raise ValueError(
                f"I don't know what to do with an event of type `{event_key}`!"
            )
        event_type_name = event_type.__qualname__.split("[")[0]
        try:
            self._events_dict[(event_type_name, event_key)] = func
        except ValueError:
            existing_func = self._events_dict[(event_type_name, event_key)]
            msg = (
                "Route {} for event type {} is already registered by function {}"
            ).format(event_key, event_type_name, existing_func.__qualname__)
            raise ExistingRouteError(msg) from None

    @overload
    def direct_invocation(
        self, trigger_name: str, raw: Literal[False] = False
    ) -> Callable[[TypedCallable[DirectInvocationEvent, _P]], AwsEventRawCallable]:
        ...

    @overload
    def direct_invocation(
        self, trigger_name: str, raw: Literal[True]
    ) -> Callable[[DictCallable], AwsEventRawCallable]:
        ...

    def direct_invocation(
        self, trigger_name: str, raw: Bool = False
    ) -> Union[
        Callable[[TypedCallable[DirectInvocationEvent, _P]], AwsEventRawCallable],
        Callable[[DictCallable], AwsEventRawCallable],
    ]:
        """Handles direct invocation events

        Parameters
        ----------
        trigger_name : str
            Name of the triggering event
        raw : bool = `False`
            Indicates that the wrapped function accepts and returns a Dict[str, Any]
            instead of a `DirectInvocationEvent` and `LambdaResponse`

        Returns
        -------
        AwsEventTypedCallable[DirectInvocationEvent]
            A callable that handles a DirectInvocationEvent, or a Dict[str, Any]

        Examples
        --------
        ```python
        from lambda_handler import (
            LambdaHandler,
            DirectInvocationEvent,
            LambdaResponse,
        )

        handler = LambdaHandler()

        @handler.direct_invocation(trigger_name="MyTrigger")
        def handle_direct_invocation(event: DirectInvocationEvent) -> LambdaResponse:
            body = frobincate()
            return LambdaResponse(status_code=200, body=body)
        ```
        """
        if raw:
            return create_wrapper(
                handler=self,
                event_type=DirectInvocationEvent,
                event_key=trigger_name,
                raw=True,
            )
        return create_wrapper(
            handler=self,
            event_type=DirectInvocationEvent,
            event_key=trigger_name,
            raw=False,
        )

    @overload
    def event_bridge(
        self, resource_name: str, raw: Literal[False] = False
    ) -> Callable[[TypedCallable[EventBridgeEvent, _P]], AwsEventRawCallable]:
        ...

    @overload
    def event_bridge(
        self, resource_name: str, raw: Literal[True]
    ) -> Callable[[DictCallable], AwsEventRawCallable]:
        ...

    def event_bridge(
        self, resource_name: str, raw: Bool = False
    ) -> Union[
        Callable[[TypedCallable[EventBridgeEvent, _P]], AwsEventRawCallable],
        Callable[[DictCallable], AwsEventRawCallable],
    ]:
        """Handles EventBridge events

        Parameters
        ----------
        resource_name : str
            Name of the triggering EventBridge resource
        raw : bool = `False`
            Indicates that the wrapped function accepts and returns a Dict[str, Any]
            instead of an `EventBridgeEvent` and `LambdaResponse`

        Returns
        -------
        AwsEventTypedCallable[EventBridgeEvent]
            A callable that handles a EventBridgeEvent, or a Dict[str, Any]

        Examples
        --------
        ```python
        handler = LambdaHandler()

        @handler.event_bridge(resource_name="MyResource")
        def handle_event_bridge(event: EventBridgeEvent) -> LambdaResponse:
            body = frobincate()
            return LambdaResponse(status_code=200, body=body)
        ```
        """

        return create_wrapper(
            handler=self,
            event_type=EventBridgeEvent,
            event_key=resource_name,
            raw=raw,
        )

    @overload
    def s3(
        self, event_name: str, raw: Literal[False]
    ) -> Callable[[TypedCallable[S3Event, _P]], AwsEventRawCallable]:
        ...

    @overload
    def s3(
        self, event_name: str, raw: Literal[True]
    ) -> Callable[[DictCallable], AwsEventRawCallable]:
        ...

    def s3(
        self, event_name: str, raw: Bool = False
    ) -> Union[
        Callable[[TypedCallable[S3Event, _P]], AwsEventRawCallable],
        Callable[[DictCallable], AwsEventRawCallable],
    ]:
        """Handles S3 events

        Parameters
        ----------
        event_name : str
            Name of the S3 event, which may be a regular expression such as `ObjectCreated:.*`
        raw : bool = `False`
            Indicates that the wrapped function accepts and returns a Dict[str, Any]
            instead of an `S3Event` and `LambdaResponse`

        Returns
        -------
        AwsEventTypedCallable[S3Event]
            A callable that handles an S3Event, or a Dict[str, Any]
        """

        return create_wrapper(
            handler=self,
            event_type=S3Event,
            event_key=event_name,
            raw=raw,
        )

    @overload
    def sns(
        self,
        topic_name: str,
        raw: Literal[False] = False,
    ) -> Callable[[TypedCallable[SnsEvent, _P]], AwsEventRawCallable]:
        ...

    @overload
    def sns(
        self,
        topic_name: str,
        raw: Literal[True],
    ) -> Callable[[DictCallable], AwsEventRawCallable]:
        ...

    def sns(
        self, topic_name: str, raw: Bool = False
    ) -> Union[
        Callable[[TypedCallable[SnsEvent, _P]], AwsEventRawCallable],
        Callable[[DictCallable], AwsEventRawCallable],
    ]:
        """Handles SNS events

        Parameters
        ----------
        topic_name : str
            SNS topic name
        raw : bool = `False`
            Indicates that the wrapped function accepts and returns a Dict[str, Any]
            instead of an `SnsEvent` and `LambdaResponse`

        Returns
        -------
        AwsEventTypedCallable[SnsEvent]
            A callable that handles an SnsEvent, or a Dict[str, Any]
        """

        return create_wrapper(
            handler=self,
            event_type=SnsEvent,
            event_key=topic_name,
            raw=raw,
        )

    @overload
    def sqs(
        self, queue_name: str, raw: Literal[False]
    ) -> Callable[[TypedCallable[SqsEvent, _P]], AwsEventRawCallable]:
        ...

    @overload
    def sqs(
        self, queue_name: str, raw: Literal[True]
    ) -> Callable[[DictCallable], AwsEventRawCallable]:
        ...

    def sqs(
        self, queue_name: str, raw: Bool = False
    ) -> Union[
        Callable[[TypedCallable[SqsEvent, _P]], AwsEventRawCallable],
        Callable[[DictCallable], AwsEventRawCallable],
    ]:
        """Handles SQS events

        Parameters
        ----------
        queue_name : str
            Name of the SQS queue
        raw : bool = `False`
            Indicates that the wrapped function accepts and returns a Dict[str, Any]
            instead of an `SqsEvent` and `LambdaResponse`

        Returns
        -------
        AwsEventTypedCallable[SqsEvent]
            A callable that handles an SqsEvent, or a Dict[str, Any]
        """

        return create_wrapper(
            handler=self,
            event_type=SqsEvent,
            event_key=queue_name,
            raw=raw,
        )
