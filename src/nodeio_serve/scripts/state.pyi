import asyncio

from fastapi import FastAPI

def remember(application: FastAPI, gate: asyncio.Semaphore) -> None: ...
