import pytest

from lambda_handler import LambdaHandler, LambdaResponse, S3Event

from .events import s3_event_dict


@pytest.fixture()
def handler() -> LambdaHandler:
    """Handler fixture

    Returns
    -------
    LambdaHandler
        Handler instance
    """
    return LambdaHandler()


def test_s3(handler: LambdaHandler) -> None:
    """Test that a function that accepts an `S3Event` and returns a `LambdaResponse`
    correctly registers on the handler and returns a `LambdaResponse`

    Parameters
    ----------
    handler: LambdaHandler
        `LambdaHandler` instance
    """

    @handler.s3(event_name="ObjectCreated.*")
    def test_func(event: S3Event) -> LambdaResponse:
        return LambdaResponse(status_code="200")

    assert isinstance(test_func(s3_event_dict), dict)

    response_dict = handler(s3_event_dict, "")

    assert LambdaResponse.parse_obj(response_dict)
