import logging
from abc import abstractmethod
from enum import Enum
from typing import Optional, Dict, List

from selenium.webdriver.edge.webdriver import WebDriver


class PageSWitcher:
    def __init__(self):
        ...

    @abstractmethod
    def switch_back(self, browser: WebDriver):
        ...


class NewPageSWitcher(PageSWitcher):
    def __init__(self, last_handle: str):
        super().__init__()
        self.last_handle = last_handle

    def switch_back(self, browser: WebDriver):
        origin_url = browser.current_url
        browser.close()
        browser.switch_to.window(self.last_handle)
        current_url = browser.current_url
        logging.info(f"[PageTracking]新标签页网页回退，网址转变[{origin_url}]->[{current_url}]")


class CurrentPageSWitcher(PageSWitcher):

    def switch_back(self, browser: WebDriver):
        origin_url = browser.current_url
        browser.back()
        current_url = browser.current_url
        logging.info(f"[PageTracking]当前标签页网页回退，网址转变[{origin_url}]->[{current_url}]")


class PageTracker:
    """
    追踪页面(链接)变化与跳转
    """

    def __init__(self):
        self.histories: Dict[str, List[PageSWitcher]] = {}  # the key type is window_handle

    def track_page_switch(self, window_handle: str, switcher: PageSWitcher):
        if window_handle not in self.histories:
            self.histories[window_handle] = []
        self.histories[window_handle].append(switcher)

    def back(self, browser: WebDriver):
        window_handle = browser.current_window_handle
        if window_handle in self.histories:
            history = self.histories[window_handle]
            if len(history) > 0:
                history.pop().switch_back(browser)
