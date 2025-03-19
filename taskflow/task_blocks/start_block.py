import logging
from typing import Dict

from taskflow.block_context import BlockContext
from taskflow.task_blocks.block import Block, BlockExecuteParams, register_block


class StartBlock(Block):

    def __init__(self, name: str, context: BlockContext, **kwargs):
        super().__init__(name, context)

    def execute(self, params: BlockExecuteParams):
        logging.info("StartBlock[{}] execute".format(self.name))

    def load_from_config(self, control_flow, config: Dict):
        pass


register_block("StartBlock", StartBlock)
