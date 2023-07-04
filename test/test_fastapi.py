import pytest

from lambda_handler import LambdaHandler
from fastapi import FastAPI


def test_fastapi():
    fastapi = FastAPI()

    handler = LambdaHandler(fastapi_app=fastapi)


def test_fastapi_again():
    handler = LambdaHandler()
    fastapi = FastAPI()
    handler.fastapi_app = fastapi
