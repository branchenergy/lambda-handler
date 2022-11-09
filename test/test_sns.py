import pytest
from pydantic import BaseModel, ValidationError

from lambda_handler import LambdaHandler, LambdaResponse, Dependency
from lambda_handler.handler import ExistingRouteError, InvalidRouteError
from lambda_handler.model import SnsEvent
from lambda_handler.utils import EventKeyMismatch

from .events import (
    another_sns_event_dict,
    bad_sns_event_dict,
    sns_event_dict,
    sns_event_model_dict,
)

from typing import Any, Dict, Iterator

#: pylint: disable=redefined-outer-name


@pytest.fixture()
def handler() -> LambdaHandler:
    """Handler fixture

    Returns
    -------
    LambdaHandler
        Handler instance
    """
    return LambdaHandler()


@pytest.mark.parametrize(
    ["topic_name", "event_dict"],
    [
        ("MyTopic", sns_event_dict),
        ("MyOtherTopic", another_sns_event_dict),
    ],
)
def test_sns(
    handler: LambdaHandler, topic_name: str, event_dict: Dict[str, Any]
) -> None:
    """Test that a function that accepts an `SnsEvent` and returns a `LambdaResponse`
    correctly registers on the handler and returns a `LambdaResponse`

    Parameters
    ----------
    handler: LambdaHandler
        `LambdaHandler` instance
    topic_name: str
        Topic name
    event_dict: Dict[str, Any]
        Event dictionary
    """

    @handler.sns(topic_name=topic_name)
    def test_func(event: SnsEvent[Dict[str, Any]]) -> LambdaResponse:
        print(event)
        return LambdaResponse(status_code="200")

    assert isinstance(test_func(event_dict), dict)

    response_dict = handler(event_dict, "")

    assert LambdaResponse.parse_obj(response_dict)


@pytest.mark.parametrize(
    ["topic_name", "event_dict"],
    [
        ("MyTopic", sns_event_model_dict),
    ],
)
def test_sns_model(
    handler: LambdaHandler, topic_name: str, event_dict: Dict[str, Any]
) -> None:
    """Test that a function that accepts an `SnsEvent` and returns a `LambdaResponse`
    correctly registers on the handler and returns a `LambdaResponse`

    Parameters
    ----------
    handler: LambdaHandler
        `LambdaHandler` instance
    topic_name: str
        Topic name
    event_dict: Dict[str, Any]
        Event dictionary
    """

    class MyModel(BaseModel):
        thing: str

    @handler.sns(topic_name=topic_name)
    def test_func(event: SnsEvent[MyModel]) -> LambdaResponse:
        assert isinstance(event.records[0].sns.message, MyModel)
        return LambdaResponse(status_code="200")

    assert isinstance(test_func(event_dict), dict)

    response_dict = handler(event_dict, "")

    assert LambdaResponse.parse_obj(response_dict)


@pytest.mark.parametrize(
    ["topic_name", "event_dict"],
    [
        ("MyTopic", sns_event_dict),
        ("MyOtherTopic", another_sns_event_dict),
    ],
)
def test_sns_raw(
    handler: LambdaHandler, topic_name: str, event_dict: Dict[str, Any]
) -> None:
    """Test that a function marked with `raw` accepts and returns
    a `Dict[str, Any]`

    Parameters
    ----------
    handler: LambdaHandler
        `LambdaHandler` instance
    topic_name: str
        Topic name
    event_dict: Dict[str, Any]
        Event dictionary
    """

    @handler.sns(topic_name=topic_name, raw=True)
    def test_func(event: Dict[str, Any]) -> Dict[str, Any]:
        return {"statusCode": "200"}

    assert isinstance(test_func(event_dict), dict)

    response_dict = handler(event_dict, "")
    print(response_dict)

    assert LambdaResponse.parse_obj(response_dict)


@pytest.mark.parametrize(
    ["topic_name", "event_dict"],
    [
        ("MyOtherTopic", sns_event_dict),
        ("MyTopic", another_sns_event_dict),
    ],
)
def test_sns_topic_mismatch(
    handler: LambdaHandler, topic_name: str, event_dict: Dict[str, Any]
) -> None:
    """Test that a function registered for a particular `topic_name` raises
    an `EventKeyMismatch` if passed and event of a different `topic_name`

    Parameters
    ----------
    handler: LambdaHandler
        `LambdaHandler` instance
    topic_name: str
        Topic name
    event_dict: Dict[str, Any]
        Event dictionary
    """

    handler = LambdaHandler()

    @handler.sns(topic_name=topic_name)
    def test_func(event: SnsEvent) -> LambdaResponse:
        return LambdaResponse(status_code="200")

    with pytest.raises(EventKeyMismatch):
        _ = test_func(event_dict)


@pytest.mark.parametrize(
    ["event_dict"],
    [
        (sns_event_dict,),
        (another_sns_event_dict,),
    ],
)
def test_sns_topic_invalid_route(
    handler: LambdaHandler, event_dict: Dict[str, Any]
) -> None:
    """Test that a handler raises an `InvalidRouteError` if there is no
    handling function for an event with a given topic name

    Parameters
    ----------
    handler: LambdaHandler
        `LambdaHandler` instance
    event_dict: Dict[str, Any]
        Event dictionary
    """

    handler = LambdaHandler()

    with pytest.raises(InvalidRouteError):
        _ = handler(event_dict, "")


def test_sns_function_overwrite_fails(handler: LambdaHandler) -> None:
    """Test that attempting to register a second handling fuction for
    a given topic name raises an `ExistingRouteError`

    Parameters
    ----------
    handler: LambdaHandler
        `LambdaHandler` instance
    """

    @handler.sns(topic_name="MyTopic")
    def test_func(event: SnsEvent) -> LambdaResponse:
        return LambdaResponse(status_code="200")

    with pytest.raises(ExistingRouteError):

        @handler.sns(topic_name="MyTopic")
        def another_test_func(event: SnsEvent) -> LambdaResponse:
            return LambdaResponse(status_code="200")


def test_sns_bad_event(handler: LambdaHandler) -> None:
    """Test that passing a bad SNS event dictionary to a handling
    function raises a `ValidationError`

    Parameters
    ----------
    handler: LambdaHandler
        `LambdaHandler` instance
    """

    @handler.sns(topic_name="MyTopic")
    def test_func(event: SnsEvent) -> LambdaResponse:
        return LambdaResponse(status_code="200")

    with pytest.raises(ValidationError):
        _ = test_func(bad_sns_event_dict)
