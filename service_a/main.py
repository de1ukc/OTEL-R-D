import os

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Service A", version="0.1.0")

SECOND_SERVICE_URL = os.getenv("SECOND_SERVICE_URL", "http://127.0.0.1:8001")
REQUEST_TIMEOUT_SECONDS = 5.0


async def request_service_b(path: str) -> httpx.Response:
    async with httpx.AsyncClient(
        base_url=SECOND_SERVICE_URL,
        timeout=REQUEST_TIMEOUT_SECONDS,
    ) as client:
        try:
            response = await client.get(path)
            response.raise_for_status()
            return response
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=504,
                detail="Service B did not respond in time",
            ) from exc
        except httpx.ConnectError as exc:
            raise HTTPException(
                status_code=503,
                detail="Service B is unavailable",
            ) from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.json().get("detail", "Service B returned an error")
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=detail,
            ) from exc


@app.get("/health")
async def health() -> dict[str, str]:
    return {"service": "service-a", "status": "ok"}


@app.get("/api/aggregate")
async def aggregate() -> dict[str, object]:
    response = await request_service_b("/api/value")
    return {
        "service": "service-a",
        "message": "Service A called service B successfully",
        "service_b": response.json(),
    }


@app.get("/api/remote-failure")
async def remote_failure() -> None:
    await request_service_b("/api/fail")


def run() -> None:
    import uvicorn

    uvicorn.run("service_a.main:app", host="127.0.0.1", port=8000, reload=True)
