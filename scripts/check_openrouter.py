from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio


def main() -> int:
    configure_utf8_stdio()
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        print("OPENROUTER_API_KEY chưa được cấu hình trong .env")
        return 1

    base_url = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    ).rstrip("/")
    try:
        response = httpx.get(
            f"{base_url}/key",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(f"OpenRouter authentication failed: HTTP {exc.response.status_code}")
        return 1
    except httpx.HTTPError as exc:
        print(f"Không thể kết nối OpenRouter: {type(exc).__name__}")
        return 1

    data = response.json().get("data", {})
    print("OpenRouter authentication: OK")
    print(f"Key label: {data.get('label', 'configured')}")
    print(f"Free tier: {data.get('is_free_tier', 'unknown')}")
    print(f"Limit remaining: {data.get('limit_remaining', 'not set')}")
    print(f"Expires at: {data.get('expires_at', 'not set')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
