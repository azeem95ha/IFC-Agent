from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from os import cpu_count

CPU_WORKERS = max(2, (cpu_count() or 1) - 1)
EXECUTOR = ThreadPoolExecutor(max_workers=CPU_WORKERS)
