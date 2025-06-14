from fastapi import FastAPI
from archi import Broker
from contextlib import asynccontextmanager

_broker: Broker | None = None

def get_broker() -> Broker:
    if _broker is None:
        raise RuntimeError("Broker is not initialized.")
    return _broker

@asynccontextmanager
async def lifespan(app : FastAPI):
    # Starts up

    global _broker
    _broker = Broker()
    yield

    # Shutting down
