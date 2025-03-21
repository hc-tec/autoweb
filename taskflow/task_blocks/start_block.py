import logging
from typing import Dict, Any

from taskflow.task_blocks.block import Block, BlockExecuteParams, register_block


class StartBlock(Block):

    def __init__(self, params: Dict[str, Any]):
        super().__init__(params)

    def execute(self, params: BlockExecuteParams):
        logging.info("StartBlock[{}] execute".format(self.name))

    def load_from_config(self, control_flow, config: Dict):
        pass


register_block("StartBlock", StartBlock)
