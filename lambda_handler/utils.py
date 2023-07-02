"""Utility functions"""

import inspect
import logging
import re
from functools import wraps

from lambda_handler.dependencies import DependencyC

#: pylint: disable=duplicate-code
from lambda_handler.model import (
    ApiGatewayEvent,
    AwsEvent,
    DirectInvocationEvent,
    EventBridgeEvent,
    LambdaResponse,
    S3Event,
    SnsEvent,
    SqsEvent,
)
from lambda_handler.types import (
    AwsEventCallable,
    AwsEventRawCallable,
    AwsEventType,
    LambdaHandlerInterface,
)

from typing import Any, Callable, Dict, List, Literal, Type, TypeVar, Union, overload
from typing_extensions import Concatenate, ParamSpec, TypeAlias

#: pylint: enable=duplicate-code


__all__ = [
    "AwsEventCallable",
    "OnetimeDictionary",
    "EventKeyMismatch",
    "validate_function_signature",
    "parse_lambda_event",
]


Bool: TypeAlias = Union[Literal[True], Literal[False]]


_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class OnetimeDictionary(dict):
    """A dictionary which only allows a key to be set once"""

    def __setitem__(self, __k: _KT, __v: _VT) -> None:
        if __k in self:
            raise ValueError(f"The key {__k} has already been registered!")
        return super().__setitem__(__k, __v)


class EventKeyMismatch(Exception):
    """Raised when a function is passed an event key for which it is not registered"""

    pass


class UnknownEventType(Exception):
    """Raised when an event is of an unknown type"""

    pass


def validate_function_signature(func: Callable, input_type: Type[AwsEvent]) -> bool:
    """Valiate the given `func` has the correct signature

    Parameters
    ----------
    func : Callable
        Function that _should_ accept a single argument of type `input_type`
        and return a `LambdaResponse`
    input_type : Type[AwsEvent]
        Input type to validate the first argument of `func`

    Returns
    -------
    bool
        `True`; otherwise raises an exception

    Raises
    ------
    ValueError
        If `func` does not have the correct signature
    """

    sig = inspect.signature(func)
    params = [
        param
        for param in sig.parameters.values()
        if not isinstance(param.default, DependencyC)
    ]

    func_name = func.__qualname__

    if not sig.return_annotation == LambdaResponse:
        raise ValueError(f"`{func_name}` does not return a `LambdaResponse` instance!")
    if not len(params) == 1:
        raise ValueError(
            f"`{func_name}` should only accept a single value besides its dependencies!"
        )
    if not issubclass(params[0].annotation, input_type):
        print(params[0].annotation)
        raise ValueError(
            f"`{func_name}` should accept a single parameter of type `{input_type}`"
        )
    return True


_P = ParamSpec("_P")


def create_raw_outer(
    handler: LambdaHandlerInterface,
    event_type: Type[AwsEventType],
    event_key: str,
) -> Callable[
    [Callable[Concatenate[Dict[str, Any], _P], Dict[str, Any]]],
    AwsEventRawCallable,
]:
    """Create a wrapper for a function that accepts a `Dict[str, Any]`
    plus dependencies, and returns a `Dict[str, Any]`

    Parameters
    ----------
    handler : LambdaHandlerInterface
        LambdaHandlerInterface instance
    event_type : Type[AwsEvent[T]]
        Event type to create the wrapper for
    event_key : str
        Event key

    Returns
    -------
    Callable[
        [Callable[Concatenate[Dict[str, Any], P], Dict[str, Any]]],
        Callable[[Dict[str, Any]], Dict[str, Any]],
    ]
        A wrapper for a function that accepts a `Dict[str, Any]`
    plus dependencies, and returns a `Dict[str, Any]`
    """

    def outer(
        func: Callable[Concatenate[Dict[str, Any], _P], Dict[str, Any]]
    ) -> AwsEventRawCallable:
        @wraps(func)
        def inner(event: Dict[str, Any]) -> Dict[str, Any]:
            sig = inspect.signature(func)
            dependencies: Dict[str, Any] = {
                k: p.default()
                for k, p in sig.parameters.items()
                if isinstance(p.default, DependencyC)
            }
            return func(event, **dependencies)

        handler.add_event_func(event_type, event_key, inner)

        return inner

    return outer


def create_typed_outer(
    handler: LambdaHandlerInterface,
    event_type: Type[AwsEventType],
    event_key: str,
) -> Callable[
    [Callable[Concatenate[AwsEventType, _P], LambdaResponse]],
    AwsEventRawCallable,
]:
    """Create the wrapper function for a typed callable

    Parameters
    ----------
    handler : LambdaHandlerInterface
        `LambdaHandlerInterface` instance
    event_type : Type[AwsEventType]
        Event type
    event_key : str
        Attribute name of the event type used for routing

    Returns
    -------
    Callable[ [Callable[Concatenate[AwsEventType, _P], LambdaResponse]], AwsEventRawCallable, ]
        _description_
    """

    def outer(
        func: Callable[Concatenate[AwsEventType, _P], LambdaResponse]
    ) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        @wraps(func)
        def inner(event: Dict[str, Any]) -> Dict[str, Any]:
            """Parses the event to the correct type and passes it to `func`

            Parameters
            ----------
            event : Dict[str, Any]
                Unprocessed event

            Returns
            -------
            LambdaResponse
                `LambdaResponse` instance
            """
            # Get the actual event type from the annotation
            sig = inspect.signature(func)
            params = list(sig.parameters.values())
            concrete_event_type = params[0].annotation

            dependencies: Dict[str, Any] = {
                k: p.default()
                for k, p in sig.parameters.items()
                if isinstance(p.default, DependencyC)
            }

            parsed_event = concrete_event_type.parse_obj(event)
            if not re.match(event_key, parsed_event.event_key):
                raise EventKeyMismatch(
                    f"Event key mismatch! `'{parsed_event.event_key}' != '{event_key}'`"
                )
            return func(parsed_event, **dependencies).dict()

        handler.add_event_func(event_type, event_key, inner)

        return inner

    return outer


@overload
def create_wrapper(
    handler: LambdaHandlerInterface,
    event_type: Type[AwsEventType],
    event_key: str,
    raw: Literal[True],
) -> Callable[
    [Callable[Concatenate[Dict[str, Any], _P], Dict[str, Any]]],
    AwsEventRawCallable,
]:
    pass


@overload
def create_wrapper(
    handler: LambdaHandlerInterface,
    event_type: Type[AwsEventType],
    event_key: str,
    raw: Literal[False],
) -> Callable[
    [Callable[Concatenate[AwsEventType, _P], LambdaResponse]],
    AwsEventRawCallable,
]:
    pass


@overload
def create_wrapper(
    handler: LambdaHandlerInterface,
    event_type: Type[AwsEventType],
    event_key: str,
    raw: Bool,
) -> Union[
    Callable[
        [Callable[Concatenate[Dict[str, Any], _P], Dict[str, Any]]],
        AwsEventRawCallable,
    ],
    Callable[
        [Callable[Concatenate[AwsEventType, _P], LambdaResponse]],
        AwsEventRawCallable,
    ],
]:
    pass


def create_wrapper(
    handler: LambdaHandlerInterface,
    event_type: Type[AwsEventType],
    event_key: str,
    raw: Bool = True,
) -> Union[
    Callable[
        [Callable[Concatenate[Dict[str, Any], _P], Dict[str, Any]]],
        AwsEventRawCallable,
    ],
    Callable[
        [Callable[Concatenate[AwsEventType, _P], LambdaResponse]],
        AwsEventRawCallable,
    ],
]:
    """Create a wrapper for a given event type

    Parameters
    ----------
    handler : LambdaHandlerInterface
        Handler instance
    event_type : Type[AwsEvent]
        Event type to create the wrapper for
    event_key : str
        Event key (topic, queue, etc.) name for storing the callable
    raw : bool = `False`
        Don't parse the event before handing it to the function, and
        assume that the function returns

    Returns
    -------
    Union[
        Callable[[AwsEventTypedCallable], AwsEventCallable],
        Callable[[AwsEventRawCallable], AwsEventRawCallable]
    ]
        A callable that wraps a callable of a given signature and returns
        it
    """

    if raw:
        return create_raw_outer(
            handler=handler,
            event_type=event_type,
            event_key=event_key,
        )
    return create_typed_outer(
        handler=handler,
        event_type=event_type,
        event_key=event_key,
    )


def parse_lambda_event(event: Dict[str, Any]) -> AwsEvent:
    """Parses a Dictionary from an lambda event to an `AwsEvent` type

    Parameters
    ----------
    event : Dict[str, Any]
        Event to parse

    Returns
    -------
    AwsEvent
        Parsed event

    Raises
    ------
    UnknownEventType
        If it cannot parse `event`
    """
    event_types: List[Type[AwsEvent]] = [
        ApiGatewayEvent,
        DirectInvocationEvent,
        EventBridgeEvent,
        S3Event,
        SnsEvent,
        SqsEvent,
    ]

    for event_type in event_types:
        if event_type.matches_event_type(event):
            name = event_type.__qualname__
            logging.info("Found %s event type", name)
            return event_type.parse_obj(event)

    raise UnknownEventType(f"Cannot parse event `{event}`!")
