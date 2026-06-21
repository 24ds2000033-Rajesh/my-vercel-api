from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Force CORS headers on every response
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
                "Access-Control-Allow-Headers": "*",
            },
        )

    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.options("/{path:path}")
async def options_handler(path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )


class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: float


# Load dataset
DATA_FILE = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    DATA = json.load(f)


def percentile(values, p=95):
    if not values:
        return 0.0

    values = sorted(values)
    k = (len(values) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(values) - 1)

    if f == c:
        return values[f]

    return values[f] + (k - f) * (values[c] - values[f])


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/")
@app.post("/api")
def check_latency(payload: LatencyRequest):

    response_data = {}

    for region in payload.regions:
        region_metrics = [
            item for item in DATA
            if item["region"].lower() == region.lower()
        ]

        if not region_metrics:
            continue

        latencies = [item["latency_ms"] for item in region_metrics]
        uptimes = [item["uptime_pct"] for item in region_metrics]

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = percentile(latencies, 95)
        avg_uptime = sum(uptimes) / len(uptimes)
        breaches = sum(
            1 for latency in latencies
            if latency > payload.threshold_ms
        )

        response_data[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 3),
            "breaches": breaches
        }

    return JSONResponse(
        content=response_data,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )
