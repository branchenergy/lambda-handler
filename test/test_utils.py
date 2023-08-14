import pytest

from lambda_handler.dependencies import Dependency
from lambda_handler.model import AwsEvent, LambdaResponse
from lambda_handler.utils import OnetimeDictionary, validate_function_signature


def my_func() -> int:
    return 1


def test_onetime_dictionary():
    d = OnetimeDictionary()
    d[0] = 0

    with pytest.raises(ValueError):
        d[0] = 0


def no_return_type():
    """A function missing a return type"""
    pass


def no_argument() -> LambdaResponse:
    """A function without an argument"""
    pass


def multiple_arguments(first, second) -> LambdaResponse:
    """A function with multiple arguemnts"""
    pass


def no_type_annotation(first) -> LambdaResponse:
    """A function no parameter annotation"""
    pass


def bad_type_annotation(first: str) -> LambdaResponse:
    """A function with a bad parameter annotation"""
    pass


@pytest.mark.parametrize(
    ["func", "match"],
    [
        (no_return_type, "does not return a `LambdaResponse` instance!"),
        (no_argument, "should only accept a single value besides its dependencies!"),
        (
            multiple_arguments,
            "should only accept a single value besides its dependencies!",
        ),
        (no_type_annotation, "should accept a single parameter of type"),
        (bad_type_annotation, "should accept a single parameter of type"),
    ],
)
def test_validate_function_signature_params(func, match):
    with pytest.raises(ValueError, match=match):
        validate_function_signature(func, AwsEvent)


def test_validate_function_signature():
    def correct_types(first: AwsEvent) -> LambdaResponse:
        pass

    assert validate_function_signature(correct_types, AwsEvent)


def test_validate_function_signature_with_dependency():
    def correct_types(
        first: AwsEvent, dependency=Dependency(my_func)
    ) -> LambdaResponse:
        pass

    assert validate_function_signature(correct_types, AwsEvent)
