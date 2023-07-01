# Lambda Handler

This project defines a Python class, `LambdaHandler`, and associated Pydantic-derived
event classes, for handling API Gateway events from a range of sources, in particular:

- Direct Invocation
- EventBridge
- SQS queues
- SNS topics

When not using the optional FastAPI support (see below), the package's only dependency
is pydantic.

## Use

```python
from lambda_handler import (
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
from lambda_handler import LambdaHandler

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

FastAPI support requires the package to be installed with optional extras:
`pip install "lambda-handler[fastapi]"`, and is built on top of the existing
[Mangum](https://mangum.io/) package.

## Model Validation

The `*Event` models lambda-handler defines use [pydantic](pydantic-docs.helpmanual.io/)
for parsing and validation, and these models are _generic_. This means that you can
pass a type argument to the class when defining your function, and it will correctly
parse the content of the event (see below) to that type. If this is confusing, it's
easier to see it in action:

```python
from lambda_handler import LambdaHandler, SnsEvent, LambdaResponse
from pydantic import BaseModel

handler = LambdaHandler()

class MyModel(BaseModel):
    thing: str

@handler.sns(topic_name=topic_name)
def test_func(event: SnsEvent[MyModel]) -> LambdaResponse:
    assert isinstance(event.records[0].sns.message, MyModel)
    return LambdaResponse(status_code="200")
```

Here, we have parametrised `SnsEvent` with `MyModel` in the signature of `test_func`,
meaning that the `message` attribute is parsed to a `MyModel` instance in the process.

### Parametrised Event Attributes

The following attributes are those which are parsed to a Pydantic model for each event
type:

| Event Type              | Parsed Attribute                  |
|:------------------------|:----------------------------------|
| `DirectInvocationEvent` | `event.direct_invocation.body`    |
| `EventBridgeEvent`      | `event.detail`                    |
| `SnsEvent`              | `event.records[i].sns.message`    |
| `SqsEvent`              | `event.records[i].body`           |


## Dealing with Raw Data

If you don't want to deal with parsed event objects, you can include the `raw=True`
parameter to any of the wrapping methods of `LambdaHandler` and write a function
that accepts and returns a `Dict[str, Any]` instead. Note that, in this case, the
event object will still be parsed by the `AwsEvent` subclasses for identification,
but the event object will be passed as-is in dictionary format to the function.

```python
from fastapi import FastAPI
from lambda_handler import LambdaHandler, SnsEvent, LambdaResponse

from typing import Any, Dict

handler = LambdaHandler()

@handler.sns(topic_name="MyTopic")
def handle_mytopic(event: SnsEvent) -> LambdaResponse:
    body = frobincate()
    return LambdaResponse(status_code=200, body=body)

@handler.sns(topic_name="MyOtherTopic". raw=True)
def handle_mytopic(event: Dict[str, Any]) -> Dict[str, Any]:
    body = frobincate()
    return {"statusCode": "200"}
```
