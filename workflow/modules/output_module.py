"""输出模块类

包含OutputModule类，用于将上下文中的变量值作为工作流的输出点。
"""

from typing import Dict, Any, List, Optional
from ..module_context import ModuleExecutionResult
from ..module_port import InputDefinition, OutputDefinition, ValueType, ModuleInputs, ModuleOutputs, PortValue, InputParameter
from .module_base import ModuleMeta, ModuleType
from .atomic_module import AtomicModule


class OutputModule(AtomicModule):
    """输出模块
    
    用于从模块上下文中获取变量值，作为整个工作流的输出点。
    该模块不执行实际的业务逻辑，仅负责数据收集和转换。
    """
    
    def __init__(self, module_id: str):
        """初始化输出模块
        
        Args:
            module_id: 模块ID
        """
        super().__init__(module_id)
        self.module_type = ModuleType.OUTPUT_NODE
        
        # 设置元数据
        self.set_meta(ModuleMeta(
            title="输出节点",
            description="工作流输出数据节点，用于收集并输出数据",
            category="control",
            tags=["output", "data"]
        ))
        
        # 默认空的输入输出定义
        self.set_inputs(ModuleInputs(inputDefs=[], inputParameters=[]))
        self.set_outputs(ModuleOutputs(outputDefs=[]))
        
        
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行输出模块
        
        从上下文中获取解析好的输入参数，然后作为输出返回。
        """
        outputs = {}
        
        # 如果没有输入定义，直接返回空结果
        if not self.inputs or not self.inputs.inputDefs:
            return ModuleExecutionResult(
                success=True,
                outputs=outputs
            )
            
        # 收集所有要输出的变量值
        for input_def in self.inputs.inputDefs:
            try:
                # 从上下文获取值
                value = self.context.get_variable(self.module_id, input_def.name)
                # 添加到输出
                outputs[input_def.name] = value
            except Exception as e:
                # 输出变量未找到时，记录警告但不中断执行
                import logging
                logging.warning(f"输出变量 '{input_def.name}' 未找到: {str(e)}")
        
        return ModuleExecutionResult(
            success=True,
            outputs=outputs
        ) 