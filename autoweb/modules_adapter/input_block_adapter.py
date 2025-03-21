from typing import Dict, Any
from workflow.module_context import ModuleExecutionResult
from workflow.module_port import InputDefinition, OutputDefinition, ValueType, ModuleInputs, ModuleOutputs
from taskflow.task_blocks.input_block import InputBlock
from taskflow.task_blocks.block import BlockExecuteParams
import logging

from autoweb.modules_adapter.base_adapter import BlockModuleAdapter


class InputBlockAdapter(BlockModuleAdapter):
    """InputBlock 适配器 - 向页面元素输入文本"""
    
    def __init__(self, module_id: str, block_name: str = None):
        """
        初始化 InputBlock 适配器
        
        Args:
            module_id: 模块ID
            block_name: Block名称(可选)
        """
        # 在使用前，需要先注册 InputBlock 类
        if "InputBlock" not in self.BLOCK_CLASS_MAP:
            self.register_block_class("InputBlock", InputBlock)
            
        # InputBlock 特定属性
        self.xpath = None      # 输入框的xpath
        self.text = None       # 输入的文本
        self.clear_first = True  # 是否先清空输入框
            
        super().__init__(module_id, "InputBlock", block_name)
        
        # 初始化输入输出定义
        self._initialize_io_definitions()
    
    def _initialize_io_definitions(self):
        """初始化输入输出定义"""
        # InputBlock 的输入定义
        input_defs = [
            InputDefinition(
                name="xpath",
                type=ValueType.STRING,
                description="输入框的XPath",
                required=True
            ),
            InputDefinition(
                name="text",
                type=ValueType.STRING,
                description="要输入的文本",
                required=True
            ),
            InputDefinition(
                name="clear_first",
                type=ValueType.BOOLEAN,
                description="是否先清空输入框",
                required=False
            )
        ]
        
        # 设置输入输出
        self.set_inputs(ModuleInputs(
            inputDefs=input_defs,
            inputParameters=[]
        ))
        
        self.set_outputs(ModuleOutputs(
            outputDefs=[]
        ))
    
    def _prepare_execute_params(self, args: Dict[str, Any]) -> BlockExecuteParams:
        """准备Block执行参数"""
        params = super()._prepare_execute_params(args)
        
        # 设置属性
        if "xpath" in args:
            self.xpath = args["xpath"]
            
        if "text" in args:
            self.text = args["text"]
            
        if "clear_first" in args:
            self.clear_first = args["clear_first"]
        
        return params
    
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行Block逻辑"""
        # 执行基类方法
        result = await super()._execute_internal()
        
        # 可以添加输入操作的额外信息
        if result.success:
            result.outputs["input_text"] = self.text
            
            # 设置清空选项
            if self.block_instance and hasattr(self.block_instance, "set_clear_first"):
                self.block_instance.set_clear_first(self.clear_first)
                
        return result 