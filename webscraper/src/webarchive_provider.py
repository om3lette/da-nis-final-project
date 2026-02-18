import logging
from datetime import date

import aiohttp
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from logger import setup_logger


class WebArchiveProvider:
    BASE_URL: str = "https://web.archive.org"

    def __init__(self, base_url: str | None = None, timeout: int = 15, dev_mode: bool = False) -> None:
        self._base_url: str = (base_url or self.BASE_URL).rstrip('/')
        self._logger = setup_logger(__name__, level=logging.DEBUG if dev_mode else logging.INFO)

        self._session: aiohttp.ClientSession = aiohttp.ClientSession()

        self._selenium = webdriver.Chrome()
        self._timeout: int = timeout

    def _web_url(self) -> str:
        return f"{self._base_url}/web"

    def _build_main_page_url(self, url: str, timestamp: str):
        return f"{self._web_url()}/{timestamp}*/{url}"

    def _build_source_page_url(self, url: str, timestamp: str):
        return f"{self._web_url()}/{timestamp}/{url}"

    def get_timestamps_by_site(self, url: str, since_year: int) -> list[str]:
        timestamps: list[str] = []
        for current_year in range(since_year, date.today().year + 1):
            self._logger.info("Fetching backup timestamps for %d...", current_year)

            archive_url: str = self._build_main_page_url(url, str(current_year))
            self._selenium.get(archive_url)
            timestamps.extend(self._parse_timestamps())

        return timestamps

    def _parse_timestamps(self) -> list[str]:
        calendar_grid = WebDriverWait(self._selenium, self._timeout).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "div.calendar-grid"))
        )
        link_elements: list[WebElement] = calendar_grid.find_elements(
            By.CSS_SELECTOR, "div.month-day-container > div.calendar-day > a"
        )

        parsed_timestamps = [
            link.get_attribute("href").replace(self._base_url, '').split('/')[2]
            for link in link_elements
            if link.get_attribute("href") is not None
        ]
        self._logger.debug(f"Parsed %d timestamps", len(parsed_timestamps))
        return parsed_timestamps

    async def get_page_by_timestamp(self, url: str, timestamp: str) -> str | None:
        archive_url: str = self._build_source_page_url(url, timestamp)
        headers = {
            "User-Agent": UserAgent().chrome
        }
        async with self._session.get(archive_url, headers=headers) as response:
            # Request that finishes with non 200 status code shall be treated as "success".
            # Some pages are ill-formed and will return 403 forbidden.
            try:
                return await response.text()
            except Exception as e:
                self._logger.error("Failed to fetch %s", timestamp)
                self._logger.error(e)
                return None

    async def close_session(self) -> None:
        await self._session.close()

    def close_selenium(self) -> None:
        self._selenium.close()
