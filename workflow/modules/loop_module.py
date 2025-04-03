"""循环模块类

包含LoopModule类，用于在工作流中执行循环操作。
"""

from typing import Optional, List, Dict, Any
from ..module_context import ModuleExecutionResult
from ..module_port import (
    ValueType, InputDefinition, OutputDefinition, 
    ModuleInputs, ModuleOutputs, InputParameter, InputHelper
)
from .module_base import Module, ModuleMeta, ModuleType
from .composite_module import CompositeModule


class LoopModule(CompositeModule):
    """循环模块
    
    循环模块接收一个数组作为输入，并基于数组的长度进行循环。
    在每次循环中，循环模块会将当前的索引和元素传递给循环体。
    """
    
    def __init__(self, module_id: str):
        super().__init__(module_id, ModuleType.LOOP)
        self.loop_array = []  # 循环数组
        self.loop_body_slot_name = "loop_body"
        # 设置默认的输入输出定义
        self.create_default_config()
        
    def create_default_config(self):
        """创建默认的配置"""
        # 设置输入定义
        input_defs = [
            InputDefinition(
                name="array",
                type=ValueType.ARRAY,
                description="要循环的数组",
                required=True
            ),
            InputDefinition(
                name="continue_on_error",
                type=ValueType.BOOLEAN,
                description="循环体执行失败时是否继续",
                required=False,
                defaultValue=True
            )
        ]
        
        # 设置输出定义
        output_defs = [
            OutputDefinition(
                name="iterations",
                type=ValueType.INTEGER,
                description="循环次数"
            ),
            OutputDefinition(
                name="results",
                type=ValueType.ARRAY,
                description="所有成功迭代的结果数组"
            )
        ]
        
        # 设置输入输出
        self.set_inputs(ModuleInputs(inputDefs=input_defs, inputParameters=[]))
        self.set_outputs(ModuleOutputs(outputDefs=output_defs))
        
        # 设置元数据
        self.set_meta(ModuleMeta(
            title="循环模块",
            description="基于数组执行循环操作",
            category="control",
            tags=["loop", "iteration", "control-flow"]
        ))
        
    def get_loop_body_slot(self) -> Optional[Module]:
        """获取循环体插槽"""
        return self.slots.get(self.loop_body_slot_name)
        
    # 以下是辅助方法，简化循环体设置
    
    def set_iterator(self, source_module_id: str, output_name: str) -> None:
        """设置循环数据来源
        
        创建从source_module_id的output_name到循环模块array输入的引用
        
        Args:
            source_module_id: 数据源模块ID
            output_name: 数据源输出名称
        """
        loop_input_param = InputParameter(
            name="array",
            input=InputHelper.create_reference_value(
                ValueType.ARRAY, 
                source_module_id, 
                output_name
            )
        )
        
        # 检查是否已有输入参数
        if not self.inputs:
            self.create_default_config()
            
        # 更新或添加输入参数
        found = False
        for i, param in enumerate(self.inputs.inputParameters):
            if param.name == "array":
                self.inputs.inputParameters[i] = loop_input_param
                found = True
                break
                
        if not found:
            self.inputs.inputParameters.append(loop_input_param)
    
    def set_loop_body(self, body_module: Module) -> None:
        """设置循环体模块
        
        简化添加循环体的操作
        
        Args:
            body_module: 循环体模块
        """
        self.add_module_to_slot(self.loop_body_slot_name, body_module)
        
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行循环模块
        
        循环执行插槽中的模块，并在每次循环中传递当前的索引和元素。
        """
        # 获取循环数组
        try:
            # 尝试从上下文中获取数组参数
            self.loop_array = self.context.get_variable(self.module_id, "array")
            if not isinstance(self.loop_array, list):
                return ModuleExecutionResult(
                    success=False,
                    outputs={},
                    error=f"输入参数 'array' 不是有效的数组"
                )
        except Exception as e:
            return ModuleExecutionResult(
                success=False,
                outputs={},
                error=f"无法获取输入数组: {str(e)}"
            )
        
        # 获取错误处理选项
        try:
            continue_on_error = self.context.get_variable(self.module_id, "continue_on_error")
        except:
            # 默认为True
            continue_on_error = True
            
        # 获取循环体插槽
        loop_body = self.get_loop_body_slot()
        if not loop_body:
            return ModuleExecutionResult(
                success=False,
                outputs={},
                error="循环体插槽未定义"
            )
            
        # 存储循环结果
        loop_results = []
        all_success = True
        
        # 遍历数组执行循环
        for index, item in enumerate(self.loop_array):
            # 创建新的循环上下文
            loop_context = self._create_child_context(loop_body, self.context)
            
            # 设置循环索引和元素到上下文
            self.context.set_variable(loop_body.module_id, "index", index)
            self.context.set_variable(loop_body.module_id, "item", item)
            
            # 为循环体设置上下文
            loop_body.set_context(loop_context)
            
            # 执行循环体
            result = await loop_body.execute()
            loop_results.append(result)
            
            # 如果循环体执行失败，根据设置决定是否继续
            if not result.success:
                all_success = False
                if not continue_on_error:
                    break
        
        # 收集所有循环体的输出
        combined_outputs = {
            "iterations": len(self.loop_array),
            "results": [result.outputs for result in loop_results if result.success]
        }
        
        return ModuleExecutionResult(
            success=all_success,
            outputs=combined_outputs,
            child_results={"loop_iterations": loop_results}
        ) 