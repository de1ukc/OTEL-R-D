from fastapi import FastAPI, HTTPException

app = FastAPI(title="Service B", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"service": "service-b", "status": "ok"}


@app.get("/api/value")
async def get_value() -> dict[str, str | int]:
    return {
        "service": "service-b",
        "message": "Value returned by service B",
        "value": 42,
    }


@app.get("/api/fail")
async def fail() -> None:
    raise HTTPException(
        status_code=503,
        detail="Service B intentionally failed to handle this request",
    )


def run() -> None:
    import uvicorn

    uvicorn.run("service_b.main:app", host="127.0.0.1", port=8001, reload=True)
