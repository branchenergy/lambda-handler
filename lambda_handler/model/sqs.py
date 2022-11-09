"""SQS Events data model"""

from __future__ import annotations

import datetime as dt

#: pylint: disable=no-name-in-module
from pydantic import Field

from .base import AwsEvent, BranchBaseModel, BranchGenericModel, DataT

from typing import Any, Dict, Generic, List, Literal, Optional

#: pylint: enable=no-name-in-module


__all__ = ["SqsRecordAttributes", "SqsMesssageAttributes", "SqsRecord", "SqsEvent"]


## SQS


class SqsRecordAttributes(BranchBaseModel):
    """SQS Record attributes

    Parameters
    ----------
    approximate_recieve_count : str
        Approximate received count
    approximate_first_receive_timestamp : dt.datetime
        Approximate first received timestamp
    message_deduplication_id : Optional[str]
        Message deduplication ID
    message_group_id : Optional[str]
        Message group ID
    sender_id : str
        Sender ID
    sent_timestamp : dt.datetime
        Sent timestamp
    sequence_number : Optional[str]
        Sequence number
    aws_trace_header : Optional[str]
        AWS trace header
    """

    approximate_receive_count: str
    approximate_first_receive_timestamp: dt.datetime
    message_deduplication_id: Optional[str]
    message_group_id: Optional[str]
    sender_id: str
    sent_timestamp: dt.datetime
    sequence_number: Optional[str]
    aws_trace_header: Optional[str] = Field(alias="AWSTraceHeader")

    class Config:
        """Model configuration"""

        alias_generator = lambda s: "".join(map(str.title, s.split("_")))  # noqa: E731


class SqsMesssageAttributes(BranchBaseModel):
    """SQS Message attributes

    Parameters
    ----------
    string_value : Optional[str]
        String value
    binary_value : Optional[str]
        Binary value
    string_list_values : List[str] = []
        List of string values
    binary_list_values : List[str] = []
        List of binary values
    data_type : str
        Data type
    """

    string_value: Optional[str]
    binary_value: Optional[str]
    string_list_values: List[str] = []
    binary_list_values: List[str] = []
    data_type: str


class SqsRecord(BranchGenericModel, Generic[DataT]):
    """An SQS Record

    Parameters
    ----------
    message_id : str
        Message ID
    receipt_handle : str
        Receipt handle
    body : str
        Message body
    attributes : SqsRecordAttributes
        Record attributes
    message_attributes : Dict[str, SqsMessageAttributes]
        Message attributes
    md5_of_body : str
        Body MD5 hash
    md5_of_message_attributes : Optional[str]
        Message attributes MD5 hash
    event_source : Literal["aws:sqs"]
        Event source; must be `"aws:sqs"`
    event_source_arn : str
        Event source ARN: the resource that generated the event
    aws_region : str
        AWS region
    """

    message_id: str
    receipt_handle: str
    body: DataT
    attributes: SqsRecordAttributes
    message_attributes: Dict[str, SqsMesssageAttributes]
    md5_of_body: str
    md5_of_message_attributes: Optional[str]
    event_source: Literal["aws:sqs"]
    event_source_arn: str = Field(alias="eventSourceARN")
    aws_region: str


class SqsEvent(AwsEvent, Generic[DataT]):
    """An SQS Event

    Parameters
    ----------
    records : List[SqsRecord]
        List of `SqsRecord` instances
    """

    records: List[SqsRecord[DataT]] = Field(alias="Records")

    @property
    def queue_name(self) -> str:
        """Queue name, defined as the ARN of the first record's event source

        Returns
        -------
        str
            Queue name
        """
        return self.records[0].event_source_arn.split(":")[-1]

    @property
    def event_key(self) -> str:
        """Event key, defined as the queue name

        Returns
        -------
        str
            Queue name
        """
        return self.queue_name

    @classmethod
    def matches_event_type(cls, event: Dict[str, Any]) -> bool:
        """Infers whether the given event is an SQS event

        Parameters
        ----------
        event : Dict[str, Any]
            Lambda event

        Returns
        -------
        bool
            `True` if `event` is an SQS event
        """

        if "Records" in event:
            records = event["Records"]
            if isinstance(records, list):
                return records[0].get("eventSource") == "aws:sqs"
        return False
