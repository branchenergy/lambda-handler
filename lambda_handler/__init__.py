"""Main package"""

#: pylint: disable=duplicate-code, unused-import

from lambda_handler.dependencies import Dependency  # noqa: F401
from lambda_handler.handler import LambdaHandler  # noqa: F401
from lambda_handler.model import (  # noqa: F401
    DirectInvocationEvent,
    EventBridgeEvent,
    LambdaResponse,
    S3Event,
    SnsEvent,
    SqsEvent,
)

__version__ = "2.0.0a3"
