"""事件触发模块类

包含EventTriggerModule类，用于在工作流中触发事件。
"""

from typing import Dict, Any
from ..module_context import ModuleExecutionResult
from ..module_port import ModuleInputs, ModuleOutputs
from .module_base import ModuleMeta, ModuleType
from .atomic_module import AtomicModule
from .composite_module import CompositeModule


class EventTriggerModule(AtomicModule):
    """事件触发模块
    
    事件触发模块用于触发特定事件，当执行到此模块时，会触发父模块中对应名称的事件。
    """
    
    def __init__(self, module_id: str, event_name: str, event_data: Dict[str, Any] = None):
        super().__init__(module_id)
        self.event_name = event_name
        self.event_data = event_data or {}
        
        # 设置元数据
        meta = ModuleMeta(
            title=f"触发事件: {event_name}",
            description=f"触发 {event_name} 事件",
            category="event"
        )
        self.set_meta(meta)
        
        # 设置默认的空输入输出
        self.set_inputs(ModuleInputs(inputDefs=[], inputParameters=[]))
        self.set_outputs(ModuleOutputs(outputDefs=[]))
        
    def set_event_data(self, event_data: Dict[str, Any]):
        """设置事件数据"""
        self.event_data = event_data
        
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行事件触发逻辑"""
        # 首先从上下文中解析事件数据
        event_data = {}
        if self.inputs and self.inputs.inputParameters:
            for param in self.inputs.inputParameters:
                try:
                    value = self.context.get_variable(self.module_id, param.name)
                    event_data[param.name] = value
                except Exception as e:
                    print(f"Warning: Failed to get event data parameter {param.name}: {str(e)}")
        
        # 合并静态事件数据和动态解析的事件数据
        merged_event_data = {**self.event_data, **event_data}
        
        # 查找父模块并触发事件
        parent = self.parent
        while parent:
            if isinstance(parent, CompositeModule):
                # 调用父模块的事件触发方法
                result = await parent.trigger_event(self.event_name, merged_event_data)
                
                # 记录事件触发结果
                return ModuleExecutionResult(
                    success=result.success,
                    outputs={
                        "event_triggered": result.outputs.get("event_triggered", False),
                        "event_name": self.event_name
                    },
                    child_results=result.child_results
                )
                
            # 向上查找父模块
            parent = parent.parent
            
        # 未找到可触发事件的父模块
        return ModuleExecutionResult(
            success=True,  # 未找到事件插槽不算失败
            outputs={
                "event_triggered": False,
                "event_name": self.event_name
            }
        ) 