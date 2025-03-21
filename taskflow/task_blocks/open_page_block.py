import logging
from typing import Dict, Any

from taskflow.task_blocks.block import Block, BlockExecuteParams, register_block


class OpenPageBlock(Block):

    def __init__(self, params: Dict[str, Any]):
        super().__init__(params)
        self._page_url = params.get("page_url", '')
        self._fullscreen = params.get("fullscreen", False)

    def execute(self, params: BlockExecuteParams):
        self.browser.open_page(self._page_url)
        if self._fullscreen:
            self.browser.maximize_window()
        logging.info("{} 打开了 {}".format(self.name, self._page_url))

    def load_from_config(self, control_flow, config: Dict):
        self._fullscreen = config.get("fullscreen", False)


register_block("OpenPageBlock", OpenPageBlock)







