import logging
from typing import Dict, Any

from selenium.webdriver.remote.webelement import WebElement

from taskflow.task_blocks.block import Block, BlockExecuteParams, register_block


def _input(element: WebElement, input_value: str):
    element.clear()
    element.send_keys(input_value)


class InputBlock(Block):

    def __init__(self, params: Dict[str, Any]):
        super().__init__(params)
        self.xpath = params.get("xpath", '')
        self.input_value = params.get("input_value", '')
        self.use_loop_item = params.get("use_loop_item", False)

    def execute(self, params: BlockExecuteParams) -> any:
        if self.use_relative_xpath:
            if params.in_loop:
                loop_xpath = params.get_loop_item(self.depth - 1)
                element = self.browser.get_element_by_xpath(loop_xpath + self.xpath)
                if self.use_loop_item:
                    loop_item = "示例-提取到的元素" + params.get_loop_item(self.depth - 1)
                    _input(element, loop_item)
                else:
                    _input(element, self.input_value)
            else:
                logging.error("relative xpath is not supported in no-loop context")
        else:
            element = self.browser.get_element_by_xpath(self.xpath)
            _input(element, self.input_value)

    def load_from_config(self, control_flow, config: Dict):
        use_relative_xpath = config.get("use_relative_xpath", "False")
        if use_relative_xpath == "True":
            self.use_relative_xpath = True
        else:
            self.use_relative_xpath = False


register_block("InputBlock", InputBlock)
