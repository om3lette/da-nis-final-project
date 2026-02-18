from typing import Generic

from pydantic import BaseModel

from parser.types import T


class MetricWithPct(BaseModel, Generic[T]):
    value: T
    pct: float