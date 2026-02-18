import re
from typing import Callable, Literal

from bs4 import BeautifulSoup, Tag
from pydantic import ValidationError

from logger import setup_logger
from parser.helpers import parse_str, parse_ram, parse_physical_cpus, parse_cpu_speed, parse_vram, parse_resolution, \
    parse_drive_space, parse_gpu
from parser.schemas.metric_with_pct import MetricWithPct
from parser.schemas.parsed_page import ParsedPageSchema
from parser.schemas.parsed_row import ParsedRowSchema
from parser.types import UpdateResult

FieldSpec = tuple[str, Callable[[dict, str, ParsedRowSchema], UpdateResult]]


class PageParser:
    STATS_ROW_ID_REGEX: re.Pattern[str] = re.compile("[a-z0-9]*_stats_row")

    KNOWN_UNHANDLED_ROWS: list[str] = [
        "processor_vendor", "amd_cpu_speeds", "msaa_support_level", "nvidia_drivers",
        "ati_drivers", "video_card_driver_name", "multi-gpu_systems", "4:3_displays_physical_size",
        "16:9_displays_physical_size", "audio_devices", "microphones", "language", "drive_type",
        "network_speed", "other_settings", "vr_headsets"
    ]
    KNOWN_POSSIBLY_MISSING_FIELDS: list[str] = ["gpu", "os"]

    def __init__(self, html: str):
        self._soup = BeautifulSoup(html, 'html.parser')
        self._logger = setup_logger(__name__)
        self._field_mapping = self._build_field_map()

    @staticmethod
    def _build_field_map() -> dict[str, FieldSpec]:
        mappings: list[tuple[list[str], FieldSpec]] = [
            (["os_version", "windows_version"], ("os", parse_str)),
            (["system_ram"], ("ram", parse_ram)),
            (["intel_cpu_speeds"], ("intel_cpu_speed", parse_cpu_speed)),
            (["physical_cpus"], ("physical_cpus", parse_physical_cpus)),
            (
                [
                    "video_card_description",
                    "directx_9_shader_model_2.0_gpus",
                    "directx_9_shader_model_2b_and_3.0_gpus",
                    "directx_10_gpus",
                    "directx_10_systems_(vista_with_directx_10_gpu)",
                    "directx_10_systems_(vista/win7_&_dx_10_gpu)",
                    "directx_11_systems_(vista/win7_&_dx_11_gpu)",
                    "directx_11_gpus"
                ],
                ("gpu", parse_gpu)
            ),
            (["vram"], ("vram", parse_vram)),
            (["primary_display_resolution"], ("primary_display_resolution", parse_resolution)),
            (["multi-monitor_desktop_resolution"], ("multi_monitor_display_resolution", parse_resolution)),
            (["free_hard_drive_space"], ("free_drive_space", parse_drive_space)),
            (["total_hard_drive_space"], ("total_drive_space", parse_drive_space)),
        ]

        field_map: dict[str, FieldSpec] = {}
        for aliases, spec in mappings:
            for alias in aliases:
                field_map[alias] = spec
        return field_map

    @staticmethod
    def _normalize_field_name(s: str) -> str:
        return s.lower().replace(' ', '_')

    @staticmethod
    def _parse_row(row: Tag) -> ParsedRowSchema | None:
        def get_subsection_value(subsection: Literal["left", "right", "right2", "mid"]) -> str | None:
            subsection_tag: Tag | None = row.find("div", class_=f"stats_col_{subsection}")
            if subsection_tag is None:
                return None
            return subsection_tag.text.strip()

        most_popular: str | None = get_subsection_value("mid")
        field_name: str | None = get_subsection_value("left")
        pct_str: str | None = get_subsection_value("right")

        if field_name is None or most_popular is None or pct_str is None or not pct_str.endswith('%'):
            return None

        return ParsedRowSchema(
            most_popular=most_popular,
            field_name=PageParser._normalize_field_name(field_name),
            pct=float(pct_str.replace('%', '')),
        )


    def _extract_rows(self, root: Tag) -> list[ParsedRowSchema] | None:
        row_tags: list[Tag] = root.find_all("div", id=self.STATS_ROW_ID_REGEX)
        if len(row_tags) == 0:
            return None
        return [
            parsed_row for row in row_tags
            if (parsed_row := self._parse_row(row)) is not None and parsed_row.most_popular != ""
        ]

    def parse(self, timestamp: str) -> ParsedPageSchema | None:
        survey_table: Tag | None = self._soup.find("div", id="main_stats")
        if survey_table is None:
            self._logger.warning("Unable to locate #main_stats table %s", timestamp)
            return None
        parsed_rows: list[ParsedRowSchema] | None = self._extract_rows(survey_table)
        if parsed_rows is None:
            self._logger.warning("Unable to parse rows %s", timestamp)
            return None
        if len(parsed_rows) == 0:
            self._logger.warning("Unable to locate rows %s", timestamp)
            return None

        parsed_page_dict: dict = {}
        for parsed_row in parsed_rows:
            field_name: str = parsed_row.field_name
            if field_name not in self._field_mapping:
                if field_name in self.KNOWN_UNHANDLED_ROWS:
                    continue
                self._logger.warning("Unknown field %s %s", field_name, timestamp)
                return None

            new_field_name, handler = self._field_mapping[field_name]
            update_result: UpdateResult = handler(parsed_page_dict, field_name, parsed_row)
            if not update_result.should_update:
                continue

            parsed_page_dict[new_field_name] = MetricWithPct(
                value=update_result.value,
                pct=parsed_row.pct
            )

        # Current behavior is to drop all rows with missing values
        for possibly_missing_field in self.KNOWN_POSSIBLY_MISSING_FIELDS:
            if parsed_page_dict.get(possibly_missing_field) is None:
                return None

        # This should not fail.
        # Thrown exception indicates incomplete parsing logic.
        # But in case of an ill-formed parsing logic
        try:
            return ParsedPageSchema.model_validate(parsed_page_dict)
        except ValidationError as e:
            self._logger.error("Failed to validate %s", timestamp)
            self._logger.error(parsed_page_dict)
            self._logger.error(e)
            return None
