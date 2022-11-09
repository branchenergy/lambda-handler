import pytest

from lambda_handler import LambdaHandler, LambdaResponse, SqsEvent

from .events import sqs_event_dict


@pytest.fixture()
def handler() -> LambdaHandler:
    """Handler fixture

    Returns
    -------
    LambdaHandler
        Handler instance
    """
    return LambdaHandler()


def test_sns(handler: LambdaHandler) -> None:
    """Test that a function that accepts an `SqsEvent` and returns a `LambdaResponse`
    correctly registers on the handler and returns a `LambdaResponse`

    Parameters
    ----------
    handler: LambdaHandler
        `LambdaHandler` instance
    """

    @handler.sqs(queue_name="my-queue")
    def test_func(event: SqsEvent[str]) -> LambdaResponse:
        return LambdaResponse(status_code="200")

    assert isinstance(test_func(sqs_event_dict), dict)

    response_dict = handler(sqs_event_dict, "")

    assert LambdaResponse.parse_obj(response_dict)
