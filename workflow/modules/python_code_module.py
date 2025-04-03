"""Python代码模块类

包含PythonCodeModule类，允许在工作流中执行自定义Python代码。
"""

import asyncio
from typing import Optional, Dict, Any
from ..module_context import ModuleExecutionResult
from ..module_port import ModuleInputs, ModuleOutputs
from ..module_types import Args, Output, CodeFunction
from .module_base import ModuleMeta
from .atomic_module import AtomicModule


class PythonCodeModule(AtomicModule):
    """Python代码模块
    
    允许用户编写Python代码来实现自定义逻辑，支持同步和异步函数。
    代码必须包含一个名为main的函数（同步或异步），接收Args参数并返回Output。
    """
    
    def __init__(self, module_id: str, code: str = ""):
        super().__init__(module_id)
        self.code_function: Optional[CodeFunction] = None
        self._compiled_code = None
        self._globals = {
            'Args': Args,
            'Output': Output,
            'asyncio': asyncio
        }
        
        if code:
            self.set_code(code)
        
        # 设置元数据
        meta = ModuleMeta(
            title="Python代码",
            description="执行自定义Python代码",
            category="code"
        )
        self.set_meta(meta)
        
    def set_code(self, code: str, description: str = ""):
        """设置要执行的Python代码
        
        Args:
            code: Python代码文本
            description: 代码描述
        """
        # 检查代码是否是异步函数
        is_async = CodeFunction.is_async_code(code)
        
        # 创建代码函数定义
        self.code_function = CodeFunction(
            code=code,
            is_async=is_async,
            description=description
        )
        
        # 编译代码
        try:
            self._compiled_code = compile(code, f'<{self.module_id}>', 'exec')
        except Exception as e:
            raise ValueError(f"Invalid Python code: {str(e)}")
            
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行Python代码
        
        Returns:
            执行结果
        """
        if not self.code_function or not self._compiled_code:
            return ModuleExecutionResult(
                success=False,
                outputs={},
                error="No code set for module"
            )
            
        try:
            # 准备执行环境
            local_vars = {}
            
            # 从上下文获取输入参数
            params = {}
            if self.inputs and self.inputs.inputParameters and self.context:
                for param in self.inputs.inputParameters:
                    try:
                        # 直接从上下文中获取已解析的值
                        value = self.context.get_variable(self.module_id, param.name)
                        params[param.name] = value
                    except Exception as e:
                        return ModuleExecutionResult(
                            success=False,
                            outputs={},
                            error=f"Failed to get parameter {param.name}: {str(e)}"
                        )
            
            # 执行代码
            exec(self._compiled_code, self._globals, local_vars)
            
            # 获取main函数
            main_func = local_vars.get('main')
            if not main_func:
                return ModuleExecutionResult(
                    success=False,
                    outputs={},
                    error="No main function defined in code"
                )
                
            # 创建参数对象
            args = Args(params=params)
            
            # 执行main函数
            # if self.code_function.is_async:
            result = await main_func(args)
            # else:
                # result = main_func(args)
                
            # 验证输出
            if not isinstance(result, dict):
                return ModuleExecutionResult(
                    success=False,
                    outputs={},
                    error="Main function must return a dictionary"
                )
                
            return ModuleExecutionResult(
                success=True,
                outputs=result
            )
            
        except Exception as e:
            return ModuleExecutionResult(
                success=False,
                outputs={},
                error=f"Code execution failed: {str(e)}"
            ) 