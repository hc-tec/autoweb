import logging
from typing import Dict, Any

from taskflow.task_blocks.block import Block, BlockExecuteParams, register_block


class RollbackBlock(Block):

    def __init__(self, params: Dict[str, Any]):
        super().__init__(params)

    def execute(self, params: BlockExecuteParams) -> any:
        self.browser.rollback_page()


register_block("RollbackBlock", RollbackBlock)









