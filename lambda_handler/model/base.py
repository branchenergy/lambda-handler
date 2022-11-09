"""Base AWS events models"""

from __future__ import annotations

import json

#: pylint: disable=no-name-in-module
from pydantic import ConstrainedStr, Field
from pydantic.generics import GenericModel

from typing import Any, Dict, Generic, Optional, TypeVar

#: pylint: enable=no-name-in-module


__all__ = [
    "ApiGatewayEvent",
    "AwsAccountNumber",
    "BranchBaseModel",
    "BranchGenericModel",
    "DataT",
    "UnparseableResposeDictionary",
    "LambdaResponse",
]


def to_camel(name: str) -> str:
    """Convert a string from snake case to camel case

    Parameters
    ----------
    name : str
        String to convert, probably in `snake_case`

    Returns
    -------
    str
        Result, in `camelCase`
    """
    first, *others = name.split("_")
    remainder = "".join(map(str.title, others))
    return first + remainder


class AwsAccountNumber(ConstrainedStr):
    """AWS Account Number"""

    min_length = 12
    max_length = 12


DataT = TypeVar("DataT")


class BranchGenericModel(GenericModel, Generic[DataT]):
    """Generic Pydantic model with standard configuration"""

    class Config:
        """Model configuration"""

        alias_generator = to_camel
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        extra = "allow"
        underscore_attrs_are_private = True


BranchBaseModel = BranchGenericModel[Any]


class AwsEvent(BranchGenericModel, Generic[DataT]):
    """Generic Pydantic model for *event* models"""

    @property
    def event_key(self) -> str:
        """The event key for this particular event type

        Returns
        -------
        str
            Event key

        Raises
        ------
        NotImplementedError
            In the base class
        """
        raise NotImplementedError()

    @classmethod
    def matches_event_type(cls, event: Dict[str, Any]) -> bool:
        """Infers whether the given event is of the type handled
        by this class

        Parameters
        ----------
        event : Dict[str, Any]
            Lambda event

        Returns
        -------
        bool
            `True` if this class handles the event `event`

        Raises
        ------
        NotImplementedError
            In the base class
        """
        raise NotImplementedError()


class ApiGatewayEvent(AwsEvent):
    """API Gateway API Proxy event; this model should not be used
    directy and isn't included in the docs; it's only used for
    identifying these event types any passing them to Mangum

    Parameters
    ----------
    event : Dict[str, Any]
        Unparsed event
    """

    __root__: Dict[str, Any] = Field(description="Unparsed event")

    @property
    def event_key(self) -> str:
        """Implement `event_key`, even though we will never call it

        Returns
        -------
        str
            Empty string
        """
        return ""

    @classmethod
    def matches_event_type(cls, event: Dict[str, Any]) -> bool:
        """Infers whether the given event is an API Gateway event

        Parameters
        ----------
        event : Dict[str, Any]
            Lambda event

        Returns
        -------
        bool
            `True` if `event` is an API Gateway event
        """
        return "pathParameters" in event


class UnparseableResposeDictionary(Exception):
    """Raised when a `LambdaResponse` cannot parse a response dictionary"""

    pass


class LambdaResponse:
    """A model for a Lambda function response

    Parameters
    ----------
    status_code
        Response status code
    body : Optional[Dict[str, Any]] = None
        Response body, by default `None`; should be a dictionary
    headers : Optional[Dict[str, Any]] = None
        Response headers, by default `None`
    """

    DEFAULT_HEADERS = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Credentials": True,
        "Content-Type": "application/json",
        "X-Requested-With": "*",
    }

    def __init__(
        self,
        status_code: str,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        self.is_base64_encoded = False
        self.status_code = status_code
        self.body = body
        self.headers = headers or self.DEFAULT_HEADERS

    @property
    def raw_body(self) -> str:
        """Raw response body

        Returns
        -------
        Response body as a JSON string
        """
        if self.body is not None:
            return json.dumps(self.body)
        return ""

    def dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary for passing back the response

        Returns
        -------
        Dict[str, Any]
            Response dictionary
        """

        return {
            "isBase64Encoded": self.is_base64_encoded,
            "statusCode": self.status_code,
            "headers": self.headers,
            "body": self.raw_body,
        }

    @classmethod
    def parse_obj(cls, obj: Dict[str, Any]) -> "LambdaResponse":
        """Parse an object as a `LambdaResponse` instance

        Parameters
        ----------
        obj : Dict[str, Any]
            Object to parse

        Returns
        -------
        LambdaResponse
            `LambdaResponse` instance

        Raises
        ------
        ValueError
            If `obj` is not a dictionary
        UnparseableResposeDictionary
            If `obj` does not have a `statusCode` key
        """
        if not isinstance(obj, dict):
            raise ValueError("Cannot parse non-dictionary objects!")
        try:
            return cls(
                status_code=obj["statusCode"],
                body=obj.get("body"),
                headers=obj.get("headers"),
            )
        except KeyError:
            raise UnparseableResposeDictionary() from None
