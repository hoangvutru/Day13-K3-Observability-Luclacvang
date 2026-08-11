"""Idempotent Langfuse prompt bootstrap and label rollback helper.

This script never prints credentials. It intentionally requires the configured
Langfuse project and only manages the prompt named by LANGFUSE_PROMPT_NAME.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio

BASELINE = "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"
CANDIDATE = (
    "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}\n"
    "Answer concisely in at most 3 sentences and cite the supplied docs."
)


def client_and_name():
    load_dotenv(REPO_ROOT / ".env")
    if not os.getenv("LANGFUSE_HOST") and os.getenv("LANGFUSE_BASE_URL"):
        os.environ["LANGFUSE_HOST"] = os.environ["LANGFUSE_BASE_URL"].strip('"')
    from langfuse import get_client

    client = get_client()
    if not client.auth_check():
        raise RuntimeError("Langfuse authentication failed; check .env without committing it")
    return client, os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat")


def bootstrap(client, name: str) -> tuple[int, int]:
    existing = client.api.prompts.list(name=name, limit=50).data
    if existing:
        baseline = client.get_prompt(name, label="baseline", cache_ttl_seconds=0)
        candidate = client.get_prompt(name, label="candidate", cache_ttl_seconds=0)
        return int(baseline.version), int(candidate.version)

    baseline = client.create_prompt(
        name=name,
        prompt=BASELINE,
        labels=["baseline", "production"],
        tags=["day13", "observability"],
        commit_message="Day 13 baseline prompt",
    )
    candidate = client.create_prompt(
        name=name,
        prompt=CANDIDATE,
        labels=["candidate"],
        tags=["day13", "observability"],
        commit_message="Day 13 concise candidate prompt",
    )
    return int(baseline.version), int(candidate.version)


def set_production(client, name: str, *, target: str) -> tuple[int, int]:
    baseline = client.get_prompt(name, label="baseline", cache_ttl_seconds=0)
    candidate = client.get_prompt(name, label="candidate", cache_ttl_seconds=0)
    baseline_labels = ["baseline"]
    candidate_labels = ["candidate"]
    if target == "baseline":
        baseline_labels.append("production")
    else:
        candidate_labels.append("production")
    client.api.prompt_version.update(name, int(baseline.version), new_labels=baseline_labels)
    client.api.prompt_version.update(name, int(candidate.version), new_labels=candidate_labels)
    return int(baseline.version), int(candidate.version)


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Manage Day 13 Langfuse prompt labels")
    parser.add_argument("action", choices=("bootstrap", "promote", "rollback", "status"))
    args = parser.parse_args()
    client, name = client_and_name()
    baseline_version, candidate_version = bootstrap(client, name)

    if args.action == "promote":
        set_production(client, name, target="candidate")
    elif args.action == "rollback":
        set_production(client, name, target="baseline")

    production = client.get_prompt(name, label="production", cache_ttl_seconds=0)
    print(f"Prompt: {name}")
    print(f"baseline=v{baseline_version}; candidate=v{candidate_version}")
    print(f"production=v{production.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
