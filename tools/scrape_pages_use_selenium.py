
from selenium import webdriver
from agentscope.service import (
    ServiceResponse,
    ServiceExecStatus
)
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from typing import List


def escape_html(text):
    """将文本中的特殊HTML字符转义。"""
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#39;",
        ">": "&gt;",
        "<": "&lt;",
    }
    return "".join(html_escape_table.get(c, c) for c in text)


def scrape_pages_use_selenium(url: str, xpaths: List[str]=None) -> ServiceResponse:
    """
    Scrape web pages use selenium. You will get html doc.
    And We use xpaths to target needed elements and reduce file size.
    Args:
        url (`str`):
            The url needed to be scrape use selenium.
        xpaths (`list of str`):
            We use xpaths to target needed elements and reduce file size
    """
    # 创建浏览器操作对象
    browser = webdriver.Edge()

    try:
        # 访问url
        browser.get(url)
        # JavaScript to remove <script>, <style>, and <svg> elements
        # remove_elements_js = """
        # var elements = document.querySelectorAll('script, style, svg, img');
        # elements.forEach(function(element) {
        #     element.remove();
        # });
        # """
        # browser.execute_script(remove_elements_js)
        # if xpaths is None:
        #     target_root = browser.page_source
        # else:
        #     # locate needed elements
        #     target_root = "<html>"
        #     for xpath in xpaths:
        #         target_element = browser.find_element(By.XPATH, xpath)
        #         screen_shot = target_element.screenshot("./screen_shot.png")
        #         element_html = target_element.get_attribute("outerHTML")
        #         target_root += element_html
        #     target_root += "</html>"
        bs_html = BeautifulSoup(browser.page_source, 'html.parser')
        output = (browser, bs_html)
        status = ServiceExecStatus.SUCCESS
    except Exception as e:
        output = str(e)
        status = ServiceExecStatus.ERROR

    return ServiceResponse(status, output)













