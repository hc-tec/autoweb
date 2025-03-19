import logging

from taskflow.block_context import BlockContext

from taskflow.task_blocks.block import Block, BlockExecuteParams, register_block


class RollbackBlock(Block):

    def __init__(self, name: str, context: BlockContext, **kwargs):
        super().__init__(name, context)

    def execute(self, params: BlockExecuteParams) -> any:
        self.browser.rollback_page()


register_block("RollbackBlock", RollbackBlock)









