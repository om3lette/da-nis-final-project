from tqdm.asyncio import tqdm_asyncio

from cache_utils import load_timestamps, store_timestamps
from config import Config
from dataset.construct_dataset import construct_dataset
from logger import setup_logger
from parser.schemas.parsed_page import PageData
from tasks.task_limiter import TaskLimiter
from tasks.parse_task import parse_task
from webarchive_provider import WebArchiveProvider

TARGET_URL: str = "http://store.steampowered.com/hwsurvey"
START_YEAR: int = 2008

async def main():
    logger = setup_logger(name="main")
    config: Config = Config.ensure_config_file()

    webarchive_provider: WebArchiveProvider = WebArchiveProvider(dev_mode=config.dev_mode)
    timestamps: list[str] = await load_timestamps(TARGET_URL)

    # Get timestamps of all available backups
    if timestamps is not None:
        logger.info("Found %d cached timestamps.", len(timestamps))

    if timestamps is None or config.force_timestamps_refetch:
        if config.force_timestamps_refetch:
            logger.info("Refetching as force_timestamps_refetch is set")
        else:
            logger.info("No cached timestamps found. Fetching timestamps.")

        timestamps = webarchive_provider.get_timestamps_by_site(TARGET_URL, START_YEAR)
        await store_timestamps(TARGET_URL, timestamps)

        logger.info("Fetched %d timestamps.", len(timestamps))

    webarchive_provider.close_selenium()

    task_limiter: TaskLimiter = TaskLimiter(max_concurrent_tasks=config.max_concurrent_tasks)
    parsed_pages: list[PageData | None] = await tqdm_asyncio.gather(*[
        task_limiter.limited_task(parse_task, webarchive_provider, TARGET_URL, timestamp)
        for timestamp in timestamps
    ])

    valid_parsed_pages: list[PageData] = [parsed_page for parsed_page in parsed_pages if parsed_page is not None]
    if len(valid_parsed_pages) == 0:
        logger.warning("No parsed pages found.")

    construct_dataset(TARGET_URL,"steam-hardware-survey_2008-2026", valid_parsed_pages)
    await webarchive_provider.close_session()



if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
