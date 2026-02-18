from collections import defaultdict
from pathlib import Path

import pandas as pd

from cache_utils import get_out_path
from parser.schemas.parsed_page import PageData


def construct_dataset(url: str, filename: str, parsed_pages: list[PageData]) -> pd.DataFrame:
    df_save_path: Path = get_out_path(url)
    df_dict: defaultdict[str, list] = defaultdict(list)

    for parsed_page in parsed_pages:
        df_dict["timestamp"].append(parsed_page.timestamp)

        parsed_page_dict = parsed_page.data.model_dump()
        parsed_page_dict["primary_display_resolution"]["value"] = parsed_page.data.primary_display_resolution.value.to_string()
        parsed_page_dict["multi_monitor_display_resolution"]["value"] = parsed_page.data.multi_monitor_display_resolution.value.to_string()

        for key in parsed_page_dict.keys():
            df_dict[key].append(parsed_page_dict[key]["value"])
            df_dict[f"{key}-pct"].append(parsed_page_dict[key]["pct"])

    df: pd.DataFrame = pd.DataFrame(df_dict)
    df.to_csv(df_save_path / f"{filename}.csv")
    df.to_excel(df_save_path / f"{filename}.xlsx")
    return df