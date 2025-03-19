import logging
from typing import Dict

from taskflow.block_context import BlockContext

from taskflow.task_blocks.block import Block, BlockExecuteParams, register_block


class OpenPageBlock(Block):

    def __init__(self, name: str, page_url: str, context: BlockContext, fullscreen: bool = False, **kwargs):
        super().__init__(name, context)
        self._page_url = page_url
        self._fullscreen = fullscreen

    def execute(self, params: BlockExecuteParams):
        self.browser.open_page(self._page_url)
        if self._fullscreen:
            self.browser.maximize_window()
        logging.info("{} 打开了 {}".format(self.name, self._page_url))

    def load_from_config(self, control_flow, config: Dict):
        self._fullscreen = config.get("fullscreen", False)


register_block("OpenPageBlock", OpenPageBlock)







