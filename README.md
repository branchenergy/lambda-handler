# Lambda Handler

This project defines a Python class, `LambdaHandler`, and associated Pydantic-derived
event classes, for handling API Gateway events from a range of sources, in particular:

- Direct Invocation
- EventBridge
- SQS queues
- SNS topics

## Usage

```python
from aws_lambda_handler import (
    LambdaHandler,
    EventBridgeEvent,
    SnsEvent,
    LambdaResponse,
)

handler = LambdaHandler()

@handler.sns(topic_name="MyTopic")
def handle_mytopic(event: SnsEvent) -> LambdaResponse:
    body = frobincate()
    return LambdaResponse(status_code=200, body=body)

@handler.event_bridge(resource_name="MyResource")
def handle_myresource(event: EventBridgeEvent) -> LambdaResponse:
    body = fizzbuzz()
    return LambdaResponse(status_code=200, body=body)
```

The handler looks after both the event parsing (so your functions should always
accept an event of some `*Event` type), and its response as a properly-formatted
dictionary.

## Combining with FastAPI

A notable omission from the events that are handled by `LambdaHandler` directly are
HTTP requests. These can be handled by an instance of `FastAPI`, as follows:

```python
from fastapi import FastAPI
from aws_lambda_handler import LambdaHandler

app = FastAPI(title="My HTTP handler")

@app.get("/")
def index():
    return "Hello, World!"

handler = LambdaHandler(fastapi_app=app)
```

The handler will then take care of everything on your behalf. If you'd prefer, you
can set `fastapi_app` later instead, and the handler will take care of that, too.

```python
from fastapi import FastAPI
from lambda_handler import LambdaHandler, SnsEvent, LambdaResponse

handler = LambdaHandler()

@handler.sns(topic_name="MyTopic")
def handle_mytopic(event: SnsEvent) -> LambdaResponse:
    body = frobincate()
    return LambdaResponse(status_code=200, body=body)


app = FastAPI(title="My HTTP handler")

@app.get("/")
def index():
    return "Hello, World!"

handler.fastapi_app = app
```
