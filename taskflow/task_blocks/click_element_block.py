import logging
from typing import Dict, List, Any

from taskflow.task_blocks.block import Block, BlockExecuteParams, register_block


class ClickElementBlock(Block):

    def __init__(self, params: Dict[str, Any]):
        super().__init__(params)
        self.xpath = params.get("xpath", '')
        self.coordinates = params.get("coordinates", None)
        self.need_track = params.get("need_track", True)
        self.use_relative_xpath = params.get("use_relative_xpath", False)
        self.use_coordinates = self.coordinates is not None

    def click(self, xpath: str):
        if self.need_track:
            self.browser.click_element_and_track(xpath)
        else:
            self.browser.click_element(xpath)
            
    def click_by_coordinates(self, coordinates: List[float]):
        if self.need_track:
            self.browser.click_by_coordinates_and_track(coordinates)
        else:
            self.browser.click_by_coordinates(coordinates)

    def execute(self, params: BlockExecuteParams) -> any:
        if self.use_coordinates:
            # 使用坐标点击
            if params.in_loop and not self.coordinates:
                # 如果在循环中并且没有指定coordinates，尝试使用循环项作为坐标
                loop_coordinates = params.get_loop_item(self.depth - 1)
                if isinstance(loop_coordinates, list) and len(loop_coordinates) == 2:
                    self.click_by_coordinates(loop_coordinates)
                else:
                    logging.error(f"无效的坐标格式: {loop_coordinates}")
            else:
                # 使用预设的坐标
                self.click_by_coordinates(self.coordinates)
        elif self.use_relative_xpath:
            # 使用相对XPath点击
            if params.in_loop:
                loop_xpath = params.get_loop_item(self.depth - 1)
                self.click(loop_xpath + self.xpath)
            else:
                logging.error("relative xpath is not supported in no-loop context")
        else:
            # 使用普通XPath点击
            self.click(self.xpath)

    def load_from_config(self, control_flow, config: Dict):
        # 处理相对XPath选项
        use_relative_xpath = config.get("use_relative_xpath", "False")
        if use_relative_xpath == "True":
            self.use_relative_xpath = True
        else:
            self.use_relative_xpath = False
            
        # 处理坐标选项
        coordinates = config.get("coordinates", None)
        if coordinates:
            self.coordinates = coordinates
            self.use_coordinates = True


register_block("ClickElementBlock", ClickElementBlock)
