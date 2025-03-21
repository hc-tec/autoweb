from typing import Dict, Any
from workflow.module_context import ModuleExecutionResult
from workflow.module_port import InputDefinition, OutputDefinition, ValueType, ModuleInputs, ModuleOutputs
from taskflow.task_blocks.click_element_block import ClickElementBlock
from taskflow.task_blocks.block import BlockExecuteParams
import logging

from autoweb.modules_adapter.base_adapter import BlockModuleAdapter


class ClickElementBlockAdapter(BlockModuleAdapter):
    """ClickElementBlock 适配器 - 点击页面元素"""
    
    def __init__(self, module_id: str, block_name: str = None):
        """
        初始化 ClickElementBlock 适配器
        
        Args:
            module_id: A模块ID
            block_name: Block名称(可选)
        """
        # 在使用前，需要先注册 ClickElementBlock 类
        if "ClickElementBlock" not in self.BLOCK_CLASS_MAP:
            self.register_block_class("ClickElementBlock", ClickElementBlock)
            
        super().__init__(module_id, "ClickElementBlock", block_name)
        
        # 初始化输入输出定义
        self._initialize_io_definitions()
    
    def _initialize_io_definitions(self):
        """初始化输入输出定义"""
        # ClickElementBlock 的输入定义
        input_defs = [
            InputDefinition(
                name="xpath",
                type=ValueType.STRING,
                description="要点击元素的XPath",
                required=True
            ),
            InputDefinition(
                name="need_track",
                type=ValueType.BOOLEAN,
                description="是否跟踪页面变化",
                required=False
            )
        ]
        
        # ClickElementBlock 的输出定义
        output_defs = [
            
        ]
        
        # 设置输入输出
        self.set_inputs(ModuleInputs(
            inputDefs=input_defs,
            inputParameters=[]
        ))
        
        self.set_outputs(ModuleOutputs(
            outputDefs=output_defs
        ))
    
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行Block逻辑"""
        # 执行基类方法
        result = await super()._execute_internal()
        
        # 由于ClickElementBlock可能没有明确的输出指示页面是否变化
        # 这里我们可以根据结果和track_page设置来提供一个估计
        if result.success:
            # 如果成功点击并且track_page为True，我们假设页面可能已变化
            result.outputs["is_page_changed"] = True
        return result 
    