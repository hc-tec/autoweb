import logging

from taskflow.block_context import BlockContext
from taskflow.task_blocks.block import Block, BlockExecuteParams, register_block
from taskflow.task_blocks.condition_block import ConditionBlock


class IfBlock(Block):

    def __init__(self, name: str, context: BlockContext, **kwargs):
        Block.__init__(self, name, context)

    def execute(self, params: BlockExecuteParams):
        if params.in_loop:
            loop_item_element = params.get_loop_item_element(self.depth - 1)
            params.set_loop_item_element(self.depth, loop_item_element)
            params.set_loop_item(self.depth, params.get_loop_item(self.depth - 1))
        for inner in self.inners:
            if not isinstance(inner, ConditionBlock): continue
            inner: ConditionBlock = inner
            if inner.should_run(params):
                inner.run(params)

    def add_condition(self, condition: ConditionBlock):
        if not isinstance(condition, ConditionBlock):
            logging.error("block must be ConditionBlock")
        self.add_inner(condition)


register_block("IfBlock", IfBlock)


