"""原子模块类

包含AtomicModule类，它表示一个具有自己执行逻辑的独立原子模块。
"""

from ..module_port import (
    ValueType, PortValue, InputParameter, InputHelper
)
from ..module_context import ModuleExecutionResult
from .module_base import Module, ModuleType


class AtomicModule(Module):
    """原子模块
    
    原子模块是直接实现业务逻辑的模块，如Python代码模块、接口调用模块等。
    """
    
    def __init__(self, module_id: str):
        super().__init__(module_id, ModuleType.ATOMIC)
        
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行模块逻辑
        
        原子模块需要重写此方法，实现具体的业务逻辑
        """
        return ModuleExecutionResult(
            success=True,
            outputs={},
            error=None
        )
        
        """设置输入参数
        
        Args:
            name: 参数名称
            port_value: 端口值
        """
        if not self.inputs:
            self.inputs = ModuleInputs(inputDefs=[], inputParameters=[])
            
        # 检查是否已存在同名参数，如存在则更新
        for param in self.inputs.inputParameters:
            if param.name == name:
                param.input = port_value
                return
                
        # 不存在则添加新参数
        param = InputParameter(name=name, input=port_value)
        self.inputs.inputParameters.append(param) 