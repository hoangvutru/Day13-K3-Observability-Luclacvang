from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.llm_factory import build_llm
from app.cli import configure_utf8_stdio


def main() -> int:
    configure_utf8_stdio()
    llm = build_llm()
    result = llm.generate("health check")
    print(f"Mock LLM: OK ({result.provider}/{result.model})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
