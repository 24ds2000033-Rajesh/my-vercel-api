from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Explicit preflight handler
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

# Your DATA here ...

class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: float


def percentile(values, p=0.95):
    values = sorted(values)
    n = len(values)

    if n == 0:
        return 0.0

    k = (n - 1) * p
    f = int(k)
    c = min(f + 1, n - 1)

    if f == c:
        return values[f]

    return values[f] + (k - f) * (values[c] - values[f])


@app.post("/")
@app.post("/api")
async def check_latency(payload: LatencyRequest):

    result = {}

    for region in payload.regions:
        rows = [r for r in DATA if r["region"] == region]

        if not rows:
            continue

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime_pct"] for r in rows]

        result[region] = {
            "avg_latency": round(sum(latencies) / len(latencies), 2),
            "p95_latency": round(percentile(latencies), 2),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 3),
            "breaches": sum(1 for x in latencies if x > payload.threshold_ms),
        }

    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*"
        }
    )
