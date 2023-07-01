"""SNS Events data model"""

from __future__ import annotations

import datetime as dt

#: pylint: disable=no-name-in-module
from pydantic import BaseModel, Field
from pydantic.networks import HttpUrl

from .base import AwsEvent, BranchGenericModel, DataT

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
)

__all__ = [
    "SnsMessage",
    "SnsMsgAttributeModel",
    "SnsRecord",
    "SnsEvent",
]


if TYPE_CHECKING:
    J = TypeVar("J")

    class Json(Generic[J]):
        """Fake `Json` class to keep mypy happy"""

        def __class_getitem__(cls, item: Type[J]) -> Type[J]:
            #: pylint: disable=unused-argument
            ...

else:
    from pydantic import Json


class SnsMsgAttributeModel(BaseModel):
    """Message attributes

    Parameters
    ----------
    type : str
        Attribute type
    value : str
        Attribute value
    """

    type: str = Field(alias="Type")
    value: str = Field(alias="Value")


class SnsMessage(BranchGenericModel, Generic[DataT]):
    """An SNS message

    Parameters
    ----------
    timestamp : dt.datetime
        Timestamp
    message : str
        Message
    """

    subject: Optional[str]
    topic_arn: str
    unsubscribe_url: HttpUrl
    type: Literal["Notification"]
    message_attributes: Optional[Dict[str, SnsMsgAttributeModel]]
    message: Union[Json[DataT], str]
    message_id: str
    signing_cert_url: HttpUrl
    signature: str
    timestamp: dt.datetime
    signature_version: str

    class Config:
        """Model configuration"""

        alias_generator = lambda s: "".join(map(str.title, s.split("_")))  # noqa: E731


class SnsRecord(BranchGenericModel, Generic[DataT]):
    """An SNS record

    Parameters
    ----------
    event_source : Literal["aws:sns"]
        Event source; must be `"aws:sns"`
    event_subscription_arn : str | None = `None`
        Event subscription ARN
    sns : SnsMessage
        Message instance
    """

    event_source: Literal["aws:sns"] = Field(alias="EventSource")
    event_version: str = Field(alias="EventVersion")
    event_subscription_arn: str | None = Field(
        alias="EventSubscriptionARN", default=None
    )
    sns: SnsMessage[DataT] = Field(alias="Sns")


class SnsEvent(AwsEvent, Generic[DataT]):
    """An SNS Event

    Parameters
    ----------
    records : List[SnsRecord]
        List of `SqsRecord` instances
    """

    records: List[SnsRecord[DataT]] = Field(alias="Records")

    @property
    def topic_name(self) -> str:
        """Topic name, defined as the event subscription ARN of the first record

        Returns
        -------
        str
            Topic name
        """
        return self.records[0].event_subscription_arn.split(":")[-1]

    @property
    def event_key(self) -> str:
        """Event key, defined as the topic name

        Returns
        -------
        str
            Topic name
        """
        return self.topic_name

    @classmethod
    def matches_event_type(cls, event: Dict[str, Any]) -> bool:
        """Infers whether the given event is an SNS event

        Parameters
        ----------
        event : Dict[str, Any]
            Lambda event

        Returns
        -------
        bool
            `True` if `event` is an SNS event
        """

        if "Records" in event:
            records = event["Records"]
            if isinstance(records, list):
                return records[0].get("Sns") is not None
        return False
