"""Store the shared semaphore where the HTTP tests read it."""

import asyncio

from fastapi import FastAPI


def remember(application: FastAPI, gate: asyncio.Semaphore) -> None:
    """Record the run limit on the application state."""
    application.state.run_semaphore = gate
