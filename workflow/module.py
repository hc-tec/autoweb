"""模块系统

此文件作为模块系统的入口点，导入并再导出所有模块类，
为了保持与现有代码的兼容性，同时维护更好的模块化结构。
"""

# 从modules包导入所有模块类
from .modules import (
    Module, ModuleType, ModuleMeta,
    AtomicModule,
    CompositeModule,
    SlotModule,
    EventTriggerModule,
    PythonCodeModule,
    LoopModule,
    CustomModule,
    InputModule,
    OutputModule,
    ModuleExecutionResult,
    ModuleContext, ModuleInputs, ModuleOutputs
)

# 重新导出所有类
__all__ = [
    'Module', 'ModuleType', 'ModuleMeta',
    'AtomicModule',
    'CompositeModule',
    'SlotModule',
    'EventTriggerModule',
    'PythonCodeModule',
    'LoopModule',
    'CustomModule',
    'InputModule',
    'OutputModule',
    'ModuleExecutionResult',
    'ModuleContext', 'ModuleInputs', 'ModuleOutputs'
]