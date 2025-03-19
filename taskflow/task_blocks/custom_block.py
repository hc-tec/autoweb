
from abc import abstractmethod
from typing import Optional

from browser.browser_automation import BrowserAutomation
from taskflow.block_context import BlockContext
from taskflow.task_blocks.block import Block, BlockExecuteParams, register_block


class CustomTool:
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, block: Block, params: BlockExecuteParams):
        ...


class CustomBlock(Block):

    def __init__(self, name: str, context: BlockContext, **kwargs):
        super().__init__(name, context)
        self.tool: Optional[CustomTool] = None

    def execute(self, params: BlockExecuteParams):
        self.tool.execute(self.browser, params)


class ExecJavaScriptTool(CustomTool):
    def __init__(self, name: str, js_script: str, **kwargs):
        super().__init__(name)
        self.js_script = js_script

    def execute(self, browser: BrowserAutomation, params: BlockExecuteParams):
        browser.execute_script(self.js_script)


class ExecJavaScriptUseLoopElementTool(CustomTool):
    def __init__(self, name: str, js_script: str, **kwargs):
        super().__init__(name)
        self.js_script = js_script

    def execute(self, block: Block, params: BlockExecuteParams):
        element = params.get_loop_item_element(block.depth)
        block.browser.execute_script(self.js_script, element)


register_block("CustomBlock", CustomBlock)
