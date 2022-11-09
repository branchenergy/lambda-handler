"""EventBridge event models"""

from __future__ import annotations

import datetime as dt
import uuid

#: pylint: disable=no-name-in-module
from pydantic import Field

from .base import AwsAccountNumber, AwsEvent, DataT

from typing import Any, Dict, Generic, List, Literal, Optional

#: pylint: enable=no-name-in-module


__all__ = ["EventBridgeResource", "EventBridgeEvent"]


## EventBridge


class EventBridgeResource(str):
    """A `str` subtype that implements the `resource_name` property"""

    @property
    def resource_name(self) -> str:
        """Resource name

        Returns
        -------
        str
            Resource name
        """
        return self.split("/")[1]


class EventBridgeEvent(AwsEvent, Generic[DataT]):
    """Event Bridge Event

    Parameters
    ----------
    version : Optional[str] = "0"
        By default, this is set to 0 (zero) in all events.
    id_ : uuid.UUID
        A Version 4 UUID that's generated for every event. You can use
        `id` to trace events as they move through rules to targets.
    detail_type : str
        Identifies, in combination with the source field, the fields and
        values that appear in the detail field.
    source : Literal["aws.events"]
        Identifies the service that generated the event; we only support
        `"aws.events"` at this point
    account : AwsAccountNumber
        12 digit AWS account number
    time : str
        The event timestamp, which can be specified by the service
        originating the event. If the event spans a time interval, the
        service can report the start time, so this value might be before
        the time the event is received.
    region : str
        AWS Region
    resources : List[EventBridgeResource]
        List of ARNs that identify the resources involved in the event
    detail : Dict[str, Any]
        A JSON object that contains information about the event.
    """

    version: Optional[str] = "0"
    id_: uuid.UUID = Field(alias="id")
    source: Literal["aws.events"]
    account: AwsAccountNumber
    time: dt.datetime
    region: str
    resources: List[EventBridgeResource]
    detail_type: str = Field(alias="detail-type")
    detail: DataT
    replay_name: Optional[str] = Field(None, alias="replay-name")

    @property
    def resource_name(self) -> str:
        """The resource name of an EventBridge event is defined as the
        resource name of its first resource

        Returns
        -------
        str
            Resource name
        """
        return self.resources[0].resource_name

    @property
    def event_key(self) -> str:
        """The event key of an EventBridge event is its resource name

        Returns
        -------
        str
            Event key
        """
        return self.resource_name

    @classmethod
    def matches_event_type(cls, event: Dict[str, Any]) -> bool:
        """Infers whether the given event is an EventBridge event

        Parameters
        ----------
        event : Dict[str, Any]
            Lambda event

        Returns
        -------
        bool
            `True` if `event` is an EventBridge event
        """
        return event.get("source") == "aws.events"
