import logging

import nh3

from cache_utils import store_page_source, load_page_source
from parser.page_parser import PageParser
from parser.schemas.parsed_page import PageData, ParsedPageSchema
from webarchive_provider import WebArchiveProvider


async def parse_task(web_archive_provider: WebArchiveProvider, url: str, timestamp: str) -> PageData | None:
    logging.debug(f"Parsing {timestamp}")
    page_source: str | None = await load_page_source(url, timestamp)

    if page_source is None:
        page_source = await web_archive_provider.get_page_by_timestamp(url, timestamp)
        if page_source is None:
            return None
        page_source = nh3.clean(
            page_source,
            tags={"div", "span"},
            attributes={
                "div": {"id", "class"},
                "span": {"class"},
            }
        )
        await store_page_source(page_source, url, timestamp)

    page_parser: PageParser = PageParser(page_source)
    parsed_page: ParsedPageSchema | None = page_parser.parse(timestamp)

    if parsed_page is None:
        return None
    return PageData(
        timestamp=timestamp,
        data=parsed_page
    )




