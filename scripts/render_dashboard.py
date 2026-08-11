"""Render the six-panel dashboard contract as a portable SVG evidence file."""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from statistics import mean

import yaml

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "logs.jsonl"
CONFIG_PATH = ROOT / "config" / "dashboard.yaml"
OUTPUT_PATH = ROOT / "submission" / "evidence" / "dashboard-runtime.svg"


def percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil((p / 100) * len(ordered)) - 1))
    return ordered[index]


def load_records() -> list[dict]:
    records = [json.loads(line) for line in LOG_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    latest = max(datetime.fromisoformat(row["ts"].replace("Z", "+00:00")) for row in records)
    cutoff = latest - timedelta(minutes=60)
    return [
        row
        for row in records
        if datetime.fromisoformat(row["ts"].replace("Z", "+00:00")) >= cutoff
    ]


def panel(x: int, y: int, title: str, unit: str, value: str, detail: str, ratio: float, healthy: bool) -> str:
    ratio = max(0.0, min(1.0, ratio))
    color = "#32d583" if healthy else "#f97066"
    return f"""
    <g transform="translate({x} {y})">
      <rect width="740" height="225" rx="18" fill="#111a2d" stroke="#263552"/>
      <text x="28" y="40" class="title">{escape(title)}</text>
      <text x="712" y="39" text-anchor="end" class="unit">{escape(unit)}</text>
      <text x="28" y="105" class="value">{escape(value)}</text>
      <text x="28" y="139" class="detail">{escape(detail)}</text>
      <rect x="28" y="170" width="684" height="18" rx="9" fill="#25324a"/>
      <rect x="28" y="170" width="{684 * ratio:.1f}" height="18" rx="9" fill="{color}"/>
      <circle cx="700" cy="28" r="6" fill="{color}"/>
    </g>"""


def main() -> None:
    records = load_records()
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["dashboard"]
    received = [row for row in records if row.get("event") == "request_received"]
    responses = [row for row in records if row.get("event") == "response_sent"]
    failures = [row for row in records if row.get("event") == "request_failed"]
    latencies = [float(row["latency_ms"]) for row in responses]
    p50, p95, p99 = (percentile(latencies, p) for p in (50, 95, 99))
    error_rate = (len(failures) / len(received) * 100) if received else 0.0
    total_cost = sum(float(row.get("cost_usd", 0)) for row in responses)
    tokens_in = sum(int(row.get("tokens_in", 0)) for row in responses)
    tokens_out = sum(int(row.get("tokens_out", 0)) for row in responses)
    quality = mean(float(row.get("quality_score", 0)) for row in responses) if responses else 0.0
    thresholds = {item["id"]: item["threshold"]["value"] for item in config["panels"]}

    cards = [
        panel(40, 175, "Latency percentiles", "ms", f"P95  {p95:.0f}", f"P50 {p50:.0f}  ·  P99 {p99:.0f}  ·  SLO ≤ {thresholds['latency']:.0f}", p95 / thresholds["latency"], p95 <= thresholds["latency"]),
        panel(820, 175, "Request traffic", "requests / min", f"{len(received)} requests", "60-minute source window · refresh 30s", min(1, len(received) / 20), len(received) >= 1),
        panel(40, 430, "Error rate & breakdown", "%", f"{error_rate:.2f}%", f"{len(failures)} failed / {len(received)} received · SLO ≤ {thresholds['errors']}%", error_rate / thresholds["errors"] if thresholds["errors"] else 0, error_rate <= thresholds["errors"]),
        panel(820, 430, "Cost over time", "USD", f"${total_cost:.4f}", f"Window total · budget ≤ ${thresholds['cost']}", total_cost / thresholds["cost"], total_cost <= thresholds["cost"]),
        panel(40, 685, "Input and output tokens", "tokens", f"{tokens_in + tokens_out:,} total", f"Input {tokens_in:,}  ·  Output {tokens_out:,}  ·  cap {thresholds['tokens']:,}", (tokens_in + tokens_out) / thresholds["tokens"], (tokens_in + tokens_out) <= thresholds["tokens"]),
        panel(820, 685, "Quality proxy", "score 0–1", f"{quality:.3f}", f"Mean heuristic score · SLO ≥ {thresholds['quality']}", quality, quality >= thresholds["quality"]),
    ]
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
    <style>
      text {{ font-family: Inter, Segoe UI, Arial, sans-serif; fill: #f4f7fb; }}
      .kicker {{ font-size: 15px; font-weight: 700; letter-spacing: 2px; fill: #7dd3fc; }}
      .heading {{ font-size: 34px; font-weight: 750; }}
      .sub {{ font-size: 15px; fill: #94a3b8; }}
      .title {{ font-size: 18px; font-weight: 650; }}
      .unit {{ font-size: 13px; fill: #94a3b8; }}
      .value {{ font-size: 38px; font-weight: 750; }}
      .detail {{ font-size: 14px; fill: #a9b6ca; }}
    </style>
    <rect width="1600" height="950" fill="#08111f"/>
    <text x="40" y="47" class="kicker">DAY 13 · AI OBSERVABILITY</text>
    <text x="40" y="92" class="heading">Runtime health dashboard</text>
    <text x="40" y="124" class="sub">Source: data/logs.jsonl · Time range: last 60 minutes · Refresh: 30 seconds · {escape(generated)}</text>
    <text x="1560" y="92" text-anchor="end" class="heading" fill="#32d583">6 / 6</text>
    <text x="1560" y="120" text-anchor="end" class="sub">contract panels</text>
    {''.join(cards)}
    </svg>"""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Rendered {OUTPUT_PATH.relative_to(ROOT)} from {len(records)} log records")
    print(f"p95={p95:.0f}ms error_rate={error_rate:.2f}% cost=${total_cost:.4f} quality={quality:.3f}")


if __name__ == "__main__":
    main()
