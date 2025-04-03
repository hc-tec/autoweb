"""模块包

此包包含工作流系统中的所有模块类型，每个模块类型都在各自的文件中定义。
"""

# 从各模块文件导入类
from .module_base import Module, ModuleType, ModuleMeta, ModuleExecutionResult, ModuleContext, ModuleInputs, ModuleOutputs
from .atomic_module import AtomicModule
from .composite_module import CompositeModule
from .slot_module import SlotModule
from .event_trigger_module import EventTriggerModule
from .python_code_module import PythonCodeModule
from .loop_module import LoopModule
from .custom_module import CustomModule
from .input_module import InputModule
from .output_module import OutputModule

# 导出所有模块类
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