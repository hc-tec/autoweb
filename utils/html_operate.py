
from bs4 import BeautifulSoup
from typing import List
from lxml import etree

def remove_tags(bs_html: BeautifulSoup, tags: List[str]):

    for tag in tags:
        # 删除所有style标签
        for tag in bs_html.find_all(tag):
            tag.decompose()


def remove_all_attrs(bs_html: BeautifulSoup):
    # 移除所有元素的属性
    for tag in bs_html.find_all():
        # 清除当前标签的所有属性
        tag.attrs = {}


def compress_html(bs_html: BeautifulSoup):
    remove_all_attrs(bs_html)
    remove_tags(bs_html, ['style', 'script', 'svg'])

    return bs_html


def locate_html_use_xpath(html_doc: str, xpaths: []):
    # 使用lxml的html.fromstring解析HTML
    tree = etree.HTML(html_doc)
    target_html = ""
    for xpath in xpaths:
        # 使用xpath查找所有的p标签
        p_elements = tree.xpath(xpath)
        # 遍历所有找到的元素，并获取它们的HTML内容
        for p in p_elements:
            target_html += etree.tostring(p, encoding='unicode')
    return target_html













