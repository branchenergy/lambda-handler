"""Main package"""

#: pylint: disable=duplicate-code, unused-import

from lambda_handler.dependencies import Dependency  # noqa: F401
from lambda_handler.handler import LambdaHandler  # noqa: F401
from lambda_handler.model import (  # noqa: F401
    DirectInvocationEvent,
    EventBridgeEvent,
    LambdaResponse,
    SnsEvent,
    SqsEvent,
)

__version__ = "1.0.1"
