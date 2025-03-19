import logging
from typing import Optional, Dict

from taskflow.block_context import BlockContext
from taskflow.task_blocks.block import Block, BlockExecuteParams, register_block
from taskflow.task_blocks.loop_type import LoopType, get_loop_type


class LoopControl:

    def __init__(self):
        self.need_break = False
        self.need_continue = False

    def continue_loop(self):
        self.need_continue = True

    def break_loop(self):
        self.need_break = True


class LoopBlock(Block, LoopControl):

    def __init__(self, name: str, context: BlockContext, **kwargs):
        LoopControl.__init__(self)
        Block.__init__(self, name, context)
        self.loop_type: Optional[LoopType] = None

    def set_loop_type(self, loop_type: LoopType):
        self.loop_type = loop_type

    def load_from_config(self, control_flow, config: Dict):
        loop_type_class = get_loop_type(config["loop_type"]["type"])
        self.loop_type = loop_type_class(**config["loop_type"])

    def execute(self, params: BlockExecuteParams):
        if not self.loop_type:
            logging.error("LoopType is not set.")

        while self.loop_type.has_next():
            next_item = self.loop_type.get_next()
            for inner in self.inners:
                self.process_inner(inner, next_item, params)
                if self.need_continue:
                    self.need_continue = False
                    break
                if self.need_break:
                    self.need_break = False
                    return

    def process_inner(self, inner, next_item, params: BlockExecuteParams):
        # try:
        params.set_loop_item(self.depth, next_item)
        params.set_loop_item_element(self.depth, self.browser.get_element_by_xpath(next_item))
        params.in_loop = True
        params.current_loop = self

        inner.run(params)

        # except Exception as e:
        #     logging.error(f"An error occurred while processing an inner object: {e}")


register_block("LoopBlock", LoopBlock)