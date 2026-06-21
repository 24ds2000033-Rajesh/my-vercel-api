from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_methods=["POST", "GET", "OPTIONS"],
allow_headers=["Content-Type", "Authorization"],
expose_headers=["Access-Control-Allow-Origin"],
)


@app.options("/")
@app.options("/api")
async def options_handler():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )


DATA = [
    {"region":"apac","service":"analytics","latency_ms":205.66,"uptime_pct":98.256,"timestamp":20250301},
    {"region":"apac","service":"support","latency_ms":160.78,"uptime_pct":97.531,"timestamp":20250302},
    {"region":"apac","service":"analytics","latency_ms":204.55,"uptime_pct":98.274,"timestamp":20250303},
    {"region":"apac","service":"support","latency_ms":191.63,"uptime_pct":99.457,"timestamp":20250304},
    {"region":"apac","service":"catalog","latency_ms":226.92,"uptime_pct":97.776,"timestamp":20250305},
    {"region":"apac","service":"recommendations","latency_ms":121.49,"uptime_pct":98.045,"timestamp":20250306},
    {"region":"apac","service":"analytics","latency_ms":125.96,"uptime_pct":97.535,"timestamp":20250307},
    {"region":"apac","service":"payments","latency_ms":140.22,"uptime_pct":98.665,"timestamp":20250308},
    {"region":"apac","service":"catalog","latency_ms":179.24,"uptime_pct":97.897,"timestamp":20250309},
    {"region":"apac","service":"checkout","latency_ms":202.45,"uptime_pct":98.057,"timestamp":20250310},
    {"region":"apac","service":"support","latency_ms":133.41,"uptime_pct":98.443,"timestamp":20250311},
    {"region":"apac","service":"checkout","latency_ms":206.09,"uptime_pct":97.526,"timestamp":20250312},

    {"region":"emea","service":"catalog","latency_ms":203.69,"uptime_pct":97.843,"timestamp":20250301},
    {"region":"emea","service":"catalog","latency_ms":124.58,"uptime_pct":99.235,"timestamp":20250302},
    {"region":"emea","service":"support","latency_ms":144.56,"uptime_pct":98.422,"timestamp":20250303},
    {"region":"emea","service":"recommendations","latency_ms":157.24,"uptime_pct":98.608,"timestamp":20250304},
    {"region":"emea","service":"analytics","latency_ms":177.67,"uptime_pct":97.357,"timestamp":20250305},
    {"region":"emea","service":"payments","latency_ms":136.35,"uptime_pct":97.169,"timestamp":20250306},
    {"region":"emea","service":"support","latency_ms":110.75,"uptime_pct":98.924,"timestamp":20250307},
    {"region":"emea","service":"recommendations","latency_ms":168.98,"uptime_pct":98.577,"timestamp":20250308},
    {"region":"emea","service":"analytics","latency_ms":174.50,"uptime_pct":98.101,"timestamp":20250309},
    {"region":"emea","service":"support","latency_ms":142.36,"uptime_pct":99.463,"timestamp":20250310},
    {"region":"emea","service":"support","latency_ms":162.55,"uptime_pct":99.021,"timestamp":20250311},
    {"region":"emea","service":"checkout","latency_ms":164.86,"uptime_pct":99.184,"timestamp":20250312},

    {"region":"amer","service":"support","latency_ms":222.75,"uptime_pct":97.163,"timestamp":20250301},
    {"region":"amer","service":"analytics","latency_ms":160.73,"uptime_pct":98.214,"timestamp":20250302},
    {"region":"amer","service":"recommendations","latency_ms":214.47,"uptime_pct":97.877,"timestamp":20250303},
    {"region":"amer","service":"checkout","latency_ms":222.99,"uptime_pct":98.439,"timestamp":20250304},
    {"region":"amer","service":"support","latency_ms":190.21,"uptime_pct":98.604,"timestamp":20250305},
    {"region":"amer","service":"checkout","latency_ms":122.34,"uptime_pct":97.650,"timestamp":20250306},
    {"region":"amer","service":"recommendations","latency_ms":151.98,"uptime_pct":97.699,"timestamp":20250307},
    {"region":"amer","service":"catalog","latency_ms":172.01,"uptime_pct":98.760,"timestamp":20250308},
    {"region":"amer","service":"support","latency_ms":179.39,"uptime_pct":97.529,"timestamp":20250309},
    {"region":"amer","service":"analytics","latency_ms":150.72,"uptime_pct":99.126,"timestamp":20250310},
    {"region":"amer","service":"analytics","latency_ms":163.32,"uptime_pct":97.378,"timestamp":20250311},
    {"region":"amer","service":"recommendations","latency_ms":209.61,"uptime_pct":98.242,"timestamp":20250312}
]


class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: float


def percentile(values, p=95):
    values = sorted(values)

    if not values:
        return 0.0

    k = (len(values) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(values) - 1)

    if f == c:
        return values[f]

    return values[f] + (k - f) * (values[c] - values[f])


@app.get("/")
async def health():
    return {"status": "ok"}


@app.post("/")
async def check_latency(payload: LatencyRequest):
    regions = {}

    for region_name in payload.regions:
        region = region_name.lower().strip()

        rows = [r for r in DATA if r["region"] == region]

        if not rows:
            continue

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime_pct"] for r in rows]

        regions[region] = {
            "avg_latency": round(sum(latencies) / len(latencies), 2),
            "p95_latency": round(percentile(latencies, 95), 2),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 3),
            "breaches": sum(
                1 for latency in latencies
                if latency > payload.threshold_ms
            )
        }

    return {"regions": regions}
