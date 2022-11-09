"""Events tests"""
import json
from pathlib import Path

__all__ = [
    "direct_invocation_event_dict",
    "direct_invocation_event_model_dict",
    "sns_event_dict",
    "sns_event_model_dict",
    "another_sns_event_dict",
    "bad_sns_event_dict",
    "sqs_event_dict",
]

events_path = Path(__file__).parent

sns_event_dict = json.loads((events_path / "snsEvent.json").read_text(encoding="utf-8"))
sns_event_model_dict = json.loads(
    (events_path / "snsEventModel.json").read_text(encoding="utf-8")
)
another_sns_event_dict = json.loads(
    (events_path / "snsEventAnother.json").read_text(encoding="utf-8")
)
bad_sns_event_dict = json.loads(
    (events_path / "snsEventBad.json").read_text(encoding="utf-8")
)
sqs_event_dict = json.loads((events_path / "sqsEvent.json").read_text(encoding="utf-8"))

direct_invocation_event_dict = json.loads(
    (events_path / "directInvocation.json").read_text(encoding="utf-8")
)
direct_invocation_event_model_dict = json.loads(
    (events_path / "directInvocationModel.json").read_text(encoding="utf-8")
)
