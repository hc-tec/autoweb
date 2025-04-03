"""插槽模块类

包含SlotModule类，作为组合模块中的特定插入点。
"""

from .module_base import Module, ModuleType
from .composite_module import CompositeModule


class SlotModule(CompositeModule):
    """插槽模块
    
    插槽模块作为组合模块中的特定插入点，可以包含一系列子模块。
    当组合模块执行到插槽模块时，会依次执行插槽中的所有子模块。
    """
    
    def __init__(self, module_id: str):
        super().__init__(module_id, ModuleType.SLOT)
        self.modules = []  # 插槽中的模块列表
        
    def add_module(self, module: Module) -> bool:
        """添加模块到插槽中"""
        module.parent = self
        self.modules.append(module)
        return True
        
    async def _execute_internal(self):
        """执行插槽中的所有模块"""
        from ..module_context import ModuleExecutionResult
        
        if not self.modules:
            return ModuleExecutionResult(
                success=True,
                outputs={},
                error=None
            )
            
        modules_results = []
        success = True
        
        # 依次执行插槽中的所有模块
        for module in self.modules:
            # 设置模块的上下文
            child_context = self._create_child_context(module, self.context)
            module.set_context(child_context)
            
            # 执行模块
            result = await module.execute()
            modules_results.append(result)
            
            # 如果有模块执行失败，标记整体失败
            if not result.success:
                success = False
                
        # 合并所有模块的输出
        outputs = {}
        for result in modules_results:
            if result.success and result.outputs:
                outputs.update(result.outputs)
                
        return ModuleExecutionResult(
            success=success,
            outputs=outputs,
            child_results={"modules": modules_results}
        ) 