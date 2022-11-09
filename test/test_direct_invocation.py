import pytest
from pydantic import BaseModel

from lambda_handler import LambdaHandler, LambdaResponse
from lambda_handler.model import DirectInvocationEvent

from .events import direct_invocation_event_dict, direct_invocation_event_model_dict

from typing import Any, Dict, Type

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


class MyModel(BaseModel):
    name: str


@pytest.mark.parametrize(
    ["trigger_name", "event_dict", "model", "body_class"],
    [
        ("my-trigger", direct_invocation_event_dict, DirectInvocationEvent, str),
        (
            "my-model-trigger",
            direct_invocation_event_model_dict,
            DirectInvocationEvent[MyModel],
            MyModel,
        ),
    ],
)
def test_direct_invocation(
    handler: LambdaHandler,
    trigger_name: str,
    event_dict: Dict[str, Any],
    model: Type[DirectInvocationEvent],
    body_class: Type[Any],
) -> None:
    """Test that a function that accepts an `SnsEvent` and returns a `LambdaResponse`
    correctly registers on the handler and returns a `LambdaResponse`

    Parameters
    ----------
    handler: LambdaHandler
        `LambdaHandler` instance
    trigger_name: str
        Trigger name
    event_dict: Dict[str, Any]
        Event dictionary
    model: Type[DirectInvocationEvent]
        Model type for the function; as subclass of `DirectInvocationEvent`
    body_class: Type[Any]
        Type of the direct invocation's `body` attribute
    """

    @handler.direct_invocation(trigger_name=trigger_name)
    def test_func(event: model) -> LambdaResponse:

        assert isinstance(event.direct_invocation.body, body_class)

        return LambdaResponse(status_code=200)

    assert isinstance(test_func(event_dict), dict)

    response_dict = handler(event_dict, "")

    assert LambdaResponse.parse_obj(response_dict)
