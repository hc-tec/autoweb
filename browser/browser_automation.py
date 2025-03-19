import logging
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.edge.options import Options

from browser.page_tracker import NewPageSWitcher, CurrentPageSWitcher, PageTracker


class BrowserAutomation:

    def __init__(self):
        
        options = Options()
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument('--user-data-dir=./edge_user_data')
        options.add_argument('--disable-gpu')  # 禁用GPU加速
        options.add_argument('--no-sandbox')  # 禁用沙盒模式
        options.add_argument('--disable-dev-shm-usage')  # 禁用/dev/shm使用
        options.add_argument('--disable-extensions')  # 禁用扩展
        options.add_argument('--disable-browser-side-navigation')  # 禁用浏览器侧边导航
        options.add_argument('--disable-infobars')  # 禁用信息栏
        # options.add_experimental_option('excludeSwitches', ['enable-automation'])  # 禁用自动化提示
        self.browser = webdriver.Edge(options=options)
        self.page_tracker = PageTracker()

    def open_page(self, url: str):
        self.browser.get(url)

    def track_page_switch(self):
        ...

    def rollback_page(self):
        self.page_tracker.back(self.browser)

    def click_element(self, xpath: str) -> bool:
        try:
            element = self.browser.find_element(By.XPATH, xpath)
            ActionChains(self.browser).click(element).perform()
            return True
        except Exception as e:
            logging.log(logging.DEBUG, f"元素{xpath}不存在 Exception: {e}")
            return False

    def click_element_and_track(self, xpath: str):
        self.browser.implicitly_wait(10)

        origin_handle = self.browser.current_window_handle
        origin_url = self.browser.current_url
        origin_handles_len = len(self.browser.window_handles)

        if not self.click_element(xpath):
            return

        current_handle = self.browser.current_window_handle
        current_url = self.browser.current_url
        current_handles_len = len(self.browser.window_handles)

        if origin_handles_len != current_handles_len:
            # 标签页数量不一样，说明在页面在新标签页打开
            new_handle = self.browser.window_handles[1]
            self.browser.switch_to.window(new_handle)
            current_handle = self.browser.current_window_handle
            current_url = self.browser.current_url
            self.page_tracker.track_page_switch(new_handle, NewPageSWitcher(origin_handle))
            logging.info(f"[PageTracking]新标签页打开，网址转变[{origin_url}]->[{current_url}]")
        elif current_url != origin_url:
            # 标签页数量一样，并且网址发生了变化，说明在页面在当前标签页打开
            self.page_tracker.track_page_switch(origin_handle, CurrentPageSWitcher())
            logging.info(f"[PageTracking]当前标签页打开页面，网址转变[{origin_url}]->[{current_url}]")
        if current_handle != origin_handle:
            self.browser.switch_to.window(current_handle)

    def get_element_by_xpath(self, xpath: str) -> Optional[WebElement]:
        self.browser.implicitly_wait(10)
        try:
            return self.browser.find_element(By.XPATH, xpath)
        except Exception as e:
            logging.log(logging.DEBUG, f"元素{xpath}不存在 Exception: {e}")
            return None

    def get_element_text(self, xpath: str) -> str:
        element = self.get_element_by_xpath(xpath)
        return element.text

    def execute_script(self, js_script: str, *args) -> any:
        return self.browser.execute_script(js_script, *args)

    def click_by_coordinates(self, coordinates: list) -> bool:
        """
        根据相对坐标点击元素。坐标是相对于浏览器视口的百分比，如[0.9, 0.06]。
        :param coordinates: 相对坐标，[x, y]，值范围为0-1
        :return: 是否点击成功
        """
        try:
            # 获取窗口大小
            window_width = self.browser.execute_script("return window.innerWidth")
            window_height = self.browser.execute_script("return window.innerHeight")
            
            # 计算实际坐标
            x_position = int(window_width * coordinates[0])
            y_position = int(window_height * coordinates[1])
            
            # 执行点击
            action = ActionChains(self.browser)
            action.move_by_offset(x_position, y_position).click().perform()
            action.reset_actions()  # 重置动作链，避免累计偏移
            
            logging.info(f"点击坐标: [{x_position}, {y_position}]")
            return True
        except Exception as e:
            logging.error(f"点击坐标[{coordinates}]失败: {e}")
            return False
            
    def click_by_coordinates_and_track(self, coordinates: list):
        """
        根据相对坐标点击元素并跟踪页面变化
        :param coordinates: 相对坐标，[x, y]，值范围为0-1
        """
        self.browser.implicitly_wait(10)

        origin_handle = self.browser.current_window_handle
        origin_url = self.browser.current_url
        origin_handles_len = len(self.browser.window_handles)

        if not self.click_by_coordinates(coordinates):
            return

        current_handle = self.browser.current_window_handle
        current_url = self.browser.current_url
        current_handles_len = len(self.browser.window_handles)

        if origin_handles_len != current_handles_len:
            # 标签页数量不一样，说明在页面在新标签页打开
            new_handle = self.browser.window_handles[1]
            self.browser.switch_to.window(new_handle)
            current_handle = self.browser.current_window_handle
            current_url = self.browser.current_url
            self.page_tracker.track_page_switch(new_handle, NewPageSWitcher(origin_handle))
            logging.info(f"[PageTracking]新标签页打开，网址转变[{origin_url}]->[{current_url}]")
        elif current_url != origin_url:
            # 标签页数量一样，并且网址发生了变化，说明在页面在当前标签页打开
            self.page_tracker.track_page_switch(origin_handle, CurrentPageSWitcher())
            logging.info(f"[PageTracking]当前标签页打开页面，网址转变[{origin_url}]->[{current_url}]")
        if current_handle != origin_handle:
            self.browser.switch_to.window(current_handle)

    def maximize_window(self):
        """
        将浏览器窗口最大化
        """
        try:
            self.browser.maximize_window()
            logging.info("浏览器窗口已最大化")
        except Exception as e:
            logging.error(f"浏览器窗口最大化失败: {e}")
