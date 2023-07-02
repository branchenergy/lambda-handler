"""SNS Events data model"""

from __future__ import annotations

import datetime as dt

#: pylint: disable=no-name-in-module
from pydantic import BaseModel, Field
from pydantic.networks import IPvAnyNetwork
from pydantic.types import NonNegativeFloat

from .base import AwsEvent, BranchBaseModel

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
)

__all__ = [
    "S3EventRecordGlacierRestoreEventData",
    "S3EventRecordGlacierEventData",
    "S3Identity",
    "S3RequestParameters",
    "S3ResponseElements",
    "S3OwnerIdentify",
    "S3Bucket",
    "S3Object",
    "S3Message",
    "S3EventNotificationObject",
    "S3EventNotificationEventBridgeBucket",
    "S3EventNotificationEventBridgeDetail",
    "S3EventNotificationEventBridge",
    "S3Record",
    "S3Event",
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


class S3EventRecordGlacierRestoreEventData(BaseModel):
    lifecycle_restoration_expiry_time: dt.datetime
    lifecycle_restore_storage_class: str


class S3EventRecordGlacierEventData(BaseModel):
    restore_event_data: S3EventRecordGlacierRestoreEventData


class S3Identity(BaseModel):
    principal_id: str


class S3RequestParameters(BaseModel):
    source_ip_address: IPvAnyNetwork = Field(alias="sourceIPAddress")


class S3ResponseElements(BaseModel):
    x_amz_request_id: str = Field(None, alias="x-amz-request-id")
    x_amz_id_2: str = Field(None, alias="x-amz-id-2")


class S3OwnerIdentify(BaseModel):
    principal_id: str


class S3Bucket(BaseModel):
    name: str
    owner_identity: S3OwnerIdentify
    arn: str


class S3Object(BaseModel):
    key: str
    size: Optional[NonNegativeFloat]
    etag: Optional[str] = Field(alias="eTag")
    sequencer: str
    version_id: Optional[str]


class S3Message(BaseModel):
    s3_schema_version: str
    configuration_id: str
    bucket: S3Bucket
    object: S3Object  # noqa: A003,VNE003


class S3EventNotificationObject(BaseModel):
    key: str
    size: Optional[NonNegativeFloat]
    etag: str
    version_id: str = Field(None, alias="version-id")
    sequencer: Optional[str]


class S3EventNotificationEventBridgeBucket(BaseModel):
    name: str


class S3EventNotificationEventBridgeDetail(BaseModel):
    version: str
    bucket: S3EventNotificationEventBridgeBucket
    object: S3EventNotificationObject  # noqa: A003,VNE003
    request_id: str = Field(None, alias="request-id")
    requester: str
    source_ip_address: str = Field(None, alias="source-ip-address")
    reason: Optional[str]
    deletion_type: Optional[str] = Field(None, alias="deletion-type")
    restore_expiry_time: Optional[str] = Field(None, alias="restore-expiry-time")
    source_storage_class: Optional[str] = Field(None, alias="source-storage-class")
    destination_storage_class: Optional[str] = Field(
        None, alias="destination-storage-class"
    )
    destination_access_tier: Optional[str] = Field(
        None, alias="destination-access-tier"
    )


class S3EventNotificationEventBridge(BranchBaseModel):
    version: str
    id: str  # noqa: A003,VNE003
    source: str
    account: str
    time: dt.datetime
    region: str
    resources: List[str]
    detail_type: str = Field(None, alias="detail-type")
    detail: S3EventNotificationEventBridgeDetail
    replay_name: Optional[str] = Field(None, alias="replay-name")


class S3Record(BaseModel):
    event_version: str
    event_source: Literal["aws:s3"]
    aws_region: str
    event_time: dt.datetime
    event_name: str
    user_identity: S3Identity
    request_parameters: S3RequestParameters
    response_elements: S3ResponseElements
    s3: S3Message
    glacier_event_data: Optional[S3EventRecordGlacierEventData]


class S3Event(AwsEvent):
    """An S3 event

    Parameters
    ----------
    records : List[S3Record]
        List of S3 records
    """

    records: List[S3Record]

    @property
    def event_name(self) -> str:
        """S3 event name

        Returns
        -------
        str
            Event name
        """
        return self.records[0].event_name

    @property
    def event_key(self) -> str:
        """Event key, defined as the event name

        Returns
        -------
        str
            Event name
        """
        return self.event_name

    @classmethod
    def matches_event_type(cls, event: Dict[str, Any]) -> bool:
        if "Records" in event:
            records = event["Records"]
            if isinstance(records, list):
                return records[0].get("s3", None) is not None
        return False
