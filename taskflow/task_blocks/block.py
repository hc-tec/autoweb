import logging
from abc import abstractmethod, ABC
from typing import Any, Dict, List, Optional
import keyboard
import time

from selenium.webdriver.remote.webelement import WebElement

from taskflow.block_context import BlockContext, BrowserAutomation
from taskflow.variable_system import VariableType, VariableScope


class BlockExecuteParams:
    def __init__(self):
        self.exec_result: Any = None
        self.in_loop: bool = False
        self.current_loop = None
        self.loop_item_list: List[Any] = []
        self.loop_item_element_list: List[Optional[WebElement]] = []
        self.variables: Dict[str, Any] = {}  # 用于存储执行过程中的变量值

    def set_loop_item(self, depth: int, loop_item: Any):
        while len(self.loop_item_list) < depth + 1:
            self.loop_item_list.append(None)
        self.loop_item_list[depth] = loop_item

    def get_loop_item(self, depth: int) -> Any:
        return self.loop_item_list[depth]

    def set_loop_item_element(self, depth: int, loop_item_element: WebElement):
        while len(self.loop_item_element_list) < depth + 1:
            self.loop_item_element_list.append(None)
        self.loop_item_element_list[depth] = loop_item_element

    def get_loop_item_element(self, depth: int) -> Optional[WebElement]:
        return self.loop_item_element_list[depth]

    def set_variable(self, name: str, value: Any):
        """设置变量值"""
        self.variables[name] = value

    def get_variable(self, name: str) -> Any:
        """获取变量值"""
        return self.variables.get(name, None)

    def __str__(self):
        return "BlockExecuteParams(exec_result={}, in_loop={}, current_loop={}, loop_item_list={}, " \
               "loop_item_element_list={}, variables={})".format(
            self.exec_result, self.in_loop, self.current_loop, self.loop_item_list, 
            self.loop_item_element_list, self.variables
        )


class BlockBase(ABC):
    @abstractmethod
    def run(self, *args, **kwargs):
        ...

    @abstractmethod
    def execute(self, params: BlockExecuteParams) -> any:
        ...

    @abstractmethod
    def before_execute(self, *args, **kwargs):
        ...

    @abstractmethod
    def after_execute(self, *args, **kwargs):
        ...

    @abstractmethod
    def add_inner(self, block):
        ...

    @abstractmethod
    def set_outer(self, outer):
        ...

    @abstractmethod
    def set_xpath(self, xpath: str):
        ...

    @abstractmethod
    def set_next_block(self, next_block):
        ...

    @abstractmethod
    def load_from_config(self, control_flow, config: Dict):
        ...


class Block(BlockBase):
    def __init__(self, params: Dict[str, Any]):
        self.name = params.get("name", "")
        self.xpath = params.get("xpath", '')
        self.depth = params.get("depth", 0)
        self.use_relative_xpath = params.get("use_relative_xpath", False)
        self.context: BlockContext = params.get("context", None)
        self.inners: List[BlockBase] = []
        self.next_block: Optional[BlockBase] = None
        self.outer: Optional[BlockBase] = None
        self.execute_result: Any = None
        self.breakpoint = False  # 是否在此块设置断点
        self.wait_time = 0  # 执行前等待时间（秒）
        self.input_variables: List[str] = []  # 输入变量列表
        self.output_variables: List[str] = []  # 输出变量列表

    @property
    def browser(self) -> BrowserAutomation:
        return self.context.browser

    def run(self, params: BlockExecuteParams):
        logging.debug("Run block: {}".format(self.name))
        
        # 执行前等待
        wait_time = params.get_variable("wait_time")
        if wait_time and int(wait_time) > 0 and not self.breakpoint:
            logging.info(f"等待 {wait_time} 秒后继续执行...")
            time.sleep(int(wait_time))
        
        # 处理断点
        if self.context.is_debug_mode():
            if self.breakpoint:
                logging.info(f"遇到断点: {self.name}，按F9继续...")
                self.wait_for_continue()
            
        # 处理输入变量
        # for var_name in self.input_variables:
        #     var = self.context.get_variable(var_name)
        #     if var:
        #         params.set_variable(var_name, var.get_value())
        #     else:
        #         logging.warning(f"输入变量 {var_name} 未定义")
            
        self.before_execute(params)
        
        self.execute_result = self.execute(params)
        params.exec_result = self.execute_result
        
        # 处理输出变量
        # for var_name in self.output_variables:
        #     if var_name in params.variables:
        #         self.context.set_variable_value(var_name, params.variables[var_name])
        #     else:
        #         logging.warning(f"输出变量 {var_name} 未在execute中设置")
                
        self.after_execute(params)

        if self.next_block:
            self.next_block.run(params)
            
    def wait_for_continue(self):
        """等待用户按下F9键继续执行"""
        keyboard.wait('f9')
        logging.info("继续执行...")
        
    def set_breakpoint(self, breakpoint: bool):
        """设置或取消断点"""
        self.breakpoint = breakpoint
        return self
        
    def set_wait_time(self, wait_time: float):
        """设置执行前等待时间（秒）"""
        self.wait_time = wait_time
        return self
        
    def add_input_variable(self, var_name: str):
        """添加输入变量"""
        self.input_variables.append(var_name)
        return self
        
    def add_output_variable(self, var_name: str):
        """添加输出变量"""
        self.output_variables.append(var_name)
        return self
        
    def set_input_variables(self, var_names: List[str]):
        """设置输入变量列表"""
        self.input_variables = var_names
        return self
        
    def set_output_variables(self, var_names: List[str]):
        """设置输出变量列表"""
        self.output_variables = var_names
        return self

    def execute(self, params: BlockExecuteParams) -> any:
        return NotImplementedError(
            "Please implement [{}] method".format("execute")
        )

    def load_from_config(self, control_flow, config: Dict):
        return NotImplementedError(
            "Please implement [{}] method".format("load_from_config")
        )
    
    def before_execute(self, *args, **kwargs):
        ...

    def after_execute(self, *args, **kwargs):
        ...

    def add_inner(self, block: BlockBase):
        block.outer = self
        block.depth = self.depth + 1
        self.inners.append(block)

    def set_outer(self, outer: BlockBase):
        self.outer = outer

    def set_xpath(self, xpath: str):
        self.xpath = xpath

    def set_use_relative_xpath(self, use_relative_xpath: bool):
        self.use_relative_xpath = use_relative_xpath

    def set_next_block(self, next_block: BlockBase) -> BlockBase:
        self.next_block = next_block
        next_block.depth = self.depth
        next_block.set_outer(self.outer)
        return next_block


BLOCK_MAP: Dict[str, Block] = {}


def register_block(block_type: str, block_class: Block):
    BLOCK_MAP[block_type] = block_class


class BlockFactory:

    def __init__(self, context: BlockContext):
        self.context = context

    def create_block(self, block_type: str, params: Dict[str, Any]) -> Block:
        block_class = BLOCK_MAP.get(block_type, None)
        if block_class is None:
            raise Exception("Block type {} not found".format(block_type))
        return block_class(params)
