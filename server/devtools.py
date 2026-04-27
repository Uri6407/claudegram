"""Dev-обёртка над `mcp dev server/main.py` (Inspector UI).

`uv run claudegram-dev` подымает MCP Inspector на http://localhost:6274
и подключает наш сервер. Лимитация: dev-режим не запускает наш кастомный
`_run_async` (т.е. channel-режим и permission-relay не активны), но все
119 tools / 9 resources / 6 templates / 7 prompts видны и тестируются.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run_dev() -> None:
    project_root = Path(__file__).resolve().parent.parent
    cmd = [
        "uv",
        "run",
        "mcp",
        "dev",
        str(project_root / "server" / "main.py"),
    ]
    print(f"[claudegram-dev] launching: {' '.join(cmd)}")
    print(
        "[claudegram-dev] открой http://localhost:6274 после старта Inspector. "
        "Заметь: channel-режим и permission-relay в dev НЕ работают."
    )
    env = os.environ.copy()
    env.setdefault("CLAUDEGRAM_LOG_LEVEL", "DEBUG")
    sys.exit(subprocess.call(cmd, cwd=str(project_root), env=env))
