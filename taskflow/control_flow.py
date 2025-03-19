from typing import Optional

from browser.browser_automation import BrowserAutomation
from taskflow.block_context import BlockContext
from taskflow.field_saver import FieldSaver
from taskflow.task_blocks.block import Block, BlockExecuteParams


class ControlFlow:

    def __init__(self):
        self.browser = BrowserAutomation()
        self.block_context: Optional[BlockContext] = BlockContext()
        self.start_block: Optional[Block] = None
        self.field_saver = None
        self.block_context.set_browser(self.browser)

    def set_start_block(self, block: Block):
        self.start_block = block

    def set_field_saver(self, field_saver: FieldSaver):
        self.field_saver = field_saver

    def get_field_saver(self) -> FieldSaver:
        return self.field_saver

    def enable_debug_mode(self, enable: bool = True):
        """启用或禁用调试模式"""
        self.block_context.set_debug_mode(enable)
        return self

    def run(self):
        params = BlockExecuteParams()
        self.start_block.run(params)

    def get_context(self) -> BlockContext:
        return self.block_context









