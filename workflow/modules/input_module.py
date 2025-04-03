"""输入模块类

包含InputModule类，用于接收输入并将其解析后写入上下文，作为工作流的输入点。
"""

from typing import Dict, Any, List, Optional
from ..module_context import ModuleExecutionResult
from ..module_port import InputDefinition, OutputDefinition, ValueType, ModuleInputs, ModuleOutputs
from .module_base import ModuleMeta, ModuleType
from .atomic_module import AtomicModule


class InputModule(AtomicModule):
    """输入模块
    
    用于将外部输入数据解析后写入模块上下文，作为整个工作流的输入点。
    该模块不执行实际的业务逻辑，仅负责数据传递和转换。
    """
    
    def __init__(self, module_id: str):
        """初始化输入模块
        
        Args:
            module_id: 模块ID
        """
        super().__init__(module_id)
        self.module_type = ModuleType.INPUT_NODE
        
        # 设置元数据
        self.set_meta(ModuleMeta(
            title="输入节点",
            description="工作流输入数据节点，用于接收外部输入",
            category="control",
            tags=["input", "data"]
        ))
        
        # 默认空的输入输出定义
        self.set_inputs(ModuleInputs(inputDefs=[], inputParameters=[]))
        self.set_outputs(ModuleOutputs(outputDefs=[]))
        
        
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行输入模块
        
        从上下文中获取解析好的输入参数，然后作为输出返回，
        这样这些输入就可以被其他模块引用。
        """
        outputs = {}
        
        # 如果没有输入定义，直接返回空结果
        if not self.inputs or not self.inputs.inputDefs:
            return ModuleExecutionResult(
                success=True,
                outputs=outputs
            )
            
        # 收集所有输入变量的值
        for input_def in self.inputs.inputDefs:
            try:
                # 从上下文获取值
                value = self.context.get_variable(self.module_id, input_def.name)
                # 添加到输出
                outputs[input_def.name] = value
            except Exception as e:
                # 如果是必需参数但未找到值，则返回失败
                if input_def.required:
                    return ModuleExecutionResult(
                        success=False,
                        outputs={},
                        error=f"必需的输入参数 '{input_def.name}' 未提供: {str(e)}"
                    )
                    
                # 如果有默认值，使用默认值
                if hasattr(input_def, 'defaultValue') and input_def.defaultValue is not None:
                    outputs[input_def.name] = input_def.defaultValue
        
        return ModuleExecutionResult(
            success=True,
            outputs=outputs
        ) 