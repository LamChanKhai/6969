"""Monitoring and metrics service."""

import time
import psutil
from typing import Dict, Any


_start_time = time.time()


def get_system_metrics() -> Dict[str, Any]:
    """Collect system metrics for monitoring dashboard."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "cpu_usage_percent": round(cpu_percent, 1),
        "memory_usage_percent": round(memory.percent, 1),
        "disk_usage_percent": round(disk.percent, 1),
        "active_connections": 0,
        "requests_per_minute": 0,
        "avg_response_time_ms": 0,
    }


def get_uptime() -> float:
    """Get application uptime in seconds."""
    return time.time() - _start_time
