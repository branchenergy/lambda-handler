"""Direct Invocation models"""

from __future__ import annotations

import datetime as dt

from pydantic import validator

from .base import AwsEvent, BranchGenericModel, DataT

from typing import Any, Dict, Generic, Optional

__all__ = ["DirectInvocationDetail", "DirectInvocationEvent"]


## DirectInvocation


class DirectInvocationDetail(BranchGenericModel, Generic[DataT]):
    """Direct Invocation details

    Parameters
    ----------
    trigger : str
        Invocation trigger
    body : DataT
        Body
    meta : Optional[str]
        Metadata
    """

    trigger: str
    body: DataT
    meta: Optional[str]


class DirectInvocationEvent(AwsEvent, Generic[DataT]):
    """Direct Invocation event

    Parameters
    ----------
    direct_invocation : DirectInvocationDetail
        `DirectInvocationDetail` instance
    time_stamp : dt.datetime
        Invocation timestamp
    source : str
        Invocation source
    """

    direct_invocation: DirectInvocationDetail[DataT]
    time_stamp: dt.datetime
    source: str

    @validator("time_stamp", pre=True)
    def validate_timestamp(cls, value: str) -> dt.datetime:
        """Parse the `time_stamp` attribute to a datetime

        Parameters
        ----------
        value : str
            Input value

        Returns
        -------
        dt.datetime
            Parsed datetime
        """

        #: pylint: disable=no-self-argument
        return dt.datetime.strptime(value, "%Y/%m/%d %H:%M:%S")

    @property
    def event_key(self) -> str:
        """The event key of a Direct Invocation event is its trigger

        Returns
        -------
        str
            Event key
        """
        return self.direct_invocation.trigger

    @classmethod
    def matches_event_type(cls, event: Dict[str, Any]) -> bool:
        """Infers whether the given event is a Direct Invocation event

        Parameters
        ----------
        event : Dict[str, Any]
            Lambda event

        Returns
        -------
        bool
            `True` if `event` is a Direct Invocation event
        """
        return "direct_invocation" in event
