from parser.schemas.display_resolution import DisplayResolution
from parser.schemas.metric_with_pct import MetricWithPct
from parser.schemas.parsed_row import ParsedRowSchema
from parser.types import UpdateResult


def _normalize_amount(amount: int, unit: str) -> int:
    amount = int(amount)
    unit_lower: str = unit.lower()

    if unit_lower == "gb":
        return amount * 1024
    if unit_lower == "tb":
        return amount * 1048576
    return amount

def _remove_excessive_wording(s: str) -> str:
    remove_items: list[str] = ["and", "less than", "above", "higher"]
    s = s.lower()
    for remove_item in remove_items:
        s = s.replace(remove_item, "")
    return s.strip()

def parse_str(parsed_args: dict, field_name: str, row: ParsedRowSchema) -> UpdateResult[str]:
    return UpdateResult(row.most_popular, True)

def parse_gpu(parsed_args: dict, field_name: str, row: ParsedRowSchema) -> UpdateResult[str]:
    current_value: MetricWithPct[str] | None = parsed_args.get(field_name)
    if current_value is not None and current_value.pct < row.pct:
        return UpdateResult("", False)
    return UpdateResult(row.most_popular, True)

def parse_ram(parsed_args: dict, field_name: str, row: ParsedRowSchema) -> UpdateResult[int]:
    amount, unit = _remove_excessive_wording(row.most_popular).split()
    # Some int values are written with a floating point e.g. "2.0"
    # To counter that cast to float and then to int
    return UpdateResult(_normalize_amount(int(float(amount)), unit), True)

def parse_cpu_speed(parsed_args: dict, field_name: str, row: ParsedRowSchema) -> UpdateResult[int]:
    min_bound, max_bound = row.most_popular.split(" to ")

    def _parse_clock(string: str) -> float:
        return float(string.split()[0])

    average_clock_ghz: float = _parse_clock(min_bound) + _parse_clock(max_bound) / 2
    return UpdateResult(int(average_clock_ghz * 1000), True)

def parse_physical_cpus(parsed_args: dict, field_name: str, row: ParsedRowSchema) -> UpdateResult[int]:
    return UpdateResult(int(row.most_popular.split()[0]), True)

def parse_vram(parsed_args: dict, field_name: str, row: ParsedRowSchema) -> UpdateResult[int]:
    amount, unit = row.most_popular.split()
    return UpdateResult(_normalize_amount(int(amount), unit), True)

def parse_resolution(parsed_args: dict, field_name: str, row: ParsedRowSchema) -> UpdateResult[DisplayResolution]:
    width, height = row.most_popular.split(" x ")
    return UpdateResult(DisplayResolution(width=int(width), height=int(height)), True)

def parse_drive_space(parsed_args: dict, field_name: str, row: ParsedRowSchema) -> UpdateResult[int]:
    content: str = _remove_excessive_wording(row.most_popular)
    if "to" in content:
        min_bound, max_bound = content.split(" to ")
        average_free_space: float = _normalize_amount(*min_bound.split()) + _normalize_amount(*max_bound.split()) / 2
        return UpdateResult(int(average_free_space), True)
    return UpdateResult(_normalize_amount(*content.split()), True)
