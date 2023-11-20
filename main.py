"""Load page of URL, accept all cookies and take a screenshot."""

import logging
import logging.handlers
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from playwright.sync_api import sync_playwright
import time
import toml

city = "Deurne"

# Load URLs from the config file
config_file_path = 'config.toml'
with open(config_file_path, 'r') as f:
    config = toml.load(f)

# Retrieve the URLs for the 'leuven' section
URLS = list(config[city].values())

# Directory to store resulting png images in.
dst = Path("./shots")
dst.mkdir(exist_ok=True)

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger_file_handler = logging.handlers.RotatingFileHandler(
    "status.log",
    maxBytes=1024 * 1024,
    backupCount=1,
    encoding="utf8",
)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger_file_handler.setFormatter(formatter)
logger.addHandler(logger_file_handler)

def main():
    with sync_playwright() as p:
        browser_type = p.chromium
        browser = browser_type.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 720}, locale='en-US')
        page = context.new_page()

        # Go through each URL and take a screenshot
        for streetname in config[city]:
            url = config[city][streetname][“url”]
            logger.info(f"Started to take screenshot from {url}")
            assert url.startswith(“https://www.google.com/maps/”)
            page.goto(url)
            # Replace 'Alles accepteren' with the text of the button to accept cookies in your language
            for i, el in enumerate(page.get_by_label("Alles accepteren").all()):
                try:
                    el.click()
                except Exception as e:
                    logging.debug(f"Clicked {i}th element: {str(e)}")
            page.wait_for_load_state("networkidle")
            now_utc = datetime.now(timezone.utc)
            now_local = now_utc.astimezone(ZoneInfo("Europe/Brussels"))
            timestr = now_local.strftime("%Y%m%d-%H%M%S")
            # Extract the street name from the URL for naming the screenshot
            shot_file = dst / f"{city}_{streetname}_{timestr}.png"
            page.screenshot(path=shot_file.as_posix())
            logger.info(f"Took shot {shot_file.as_posix()} on {timestr}.")

        # Close the context and browser
        context.close()
        browser.close()

if __name__ == "__main__":
    main()
