"""自定义模块类

包含CustomModule类，提供更高级的组合功能。
"""

from ..module_context import ModuleExecutionResult
from .module_base import ModuleType
from .composite_module import CompositeModule


class CustomModule(CompositeModule):
    """自定义模块
    
    自定义模块是组合模块的扩展，允许使用更多高级功能，如插槽系统。
    与普通组合模块不同，自定义模块的插槽可以是任意复杂的组合模块。
    这提供了更强的组件化和模块复用能力。
    """
    
    def __init__(self, module_id: str):
        super().__init__(module_id)
        self.module_type = ModuleType.CUSTOM  # 覆盖模块类型为CUSTOM
    
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行自定义模块
        
        自定义模块的执行逻辑与组合模块类似，但可能包含更复杂的逻辑。
        """
        # 调用基类的执行逻辑
        return await super()._execute_internal() 