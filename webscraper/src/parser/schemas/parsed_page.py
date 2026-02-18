from typing import NamedTuple

from pydantic import BaseModel

from parser.schemas.display_resolution import DisplayResolution
from parser.schemas.metric_with_pct import MetricWithPct


class PageData(NamedTuple):
    timestamp: str
    data: ParsedPageSchema


class ParsedPageSchema(BaseModel):
    os: MetricWithPct[str]
    ram: MetricWithPct[int]
    intel_cpu_speed: MetricWithPct[int]
    physical_cpus: MetricWithPct[int]
    vram: MetricWithPct[int]
    gpu: MetricWithPct[str]
    primary_display_resolution: MetricWithPct[DisplayResolution]
    multi_monitor_display_resolution: MetricWithPct[DisplayResolution]
    free_drive_space: MetricWithPct[int]
    total_drive_space: MetricWithPct[int]
