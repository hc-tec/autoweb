"""组合模块类

包含CompositeModule类，它是一个可以包含其他模块的容器模块，支持插槽和事件机制。
"""

import logging
from typing import Dict, List, Optional, Any
from ..module_context import ModuleExecutionResult
from .module_base import Module, ModuleType


class CompositeModule(Module):
    """组合模块
    
    组合模块作为容器，包含普通子模块和事件插槽。
    普通子模块按顺序执行，而事件插槽在触发时执行。
    """
    
    def __init__(self, module_id: str, module_type = ModuleType.COMPOSITE):
        super().__init__(module_id, module_type)
        self.slots: Dict[str, any] = {}  # 事件插槽字典
        self.modules: List[Module] = []  # 普通子模块列表
        
    def add_module(self, module: Module) -> bool:
        """添加普通子模块"""
        module.parent = self
        self.modules.append(module)
        return True
        
    def get_slot(self, slot_name: str):
        """获取指定名称的事件插槽"""
        return self.slots.get(slot_name)
        
    def add_module_to_slot(self, slot_name: str, module: Module) -> bool:
        """向指定事件插槽添加模块
        
        如果插槽不存在，会自动创建一个新的插槽。
        如果传入的是一个组合模块，则直接作为插槽。
        
        Args:
            slot_name: 插槽名称
            module: 要添加的模块
            
        Returns:
            是否添加成功
        """
        # 如果插槽已存在
        if slot_name in self.slots:
            slot = self.slots[slot_name]
            module.parent = slot
            slot.modules.append(module)
            return True
            
        # 如果插槽不存在，创建并添加模块
        if isinstance(module, CompositeModule):
            # 对于组合模块，直接将其作为插槽
            module.parent = self
            self.slots[slot_name] = module
            return True
        
    async def trigger_event(self, event_name: str, event_data: Dict[str, Any] = None) -> ModuleExecutionResult:
        """触发事件
        
        Args:
            event_name: 事件名称
            event_data: 事件数据
            
        Returns:
            事件处理结果
        """
        if event_name not in self.slots:
            return ModuleExecutionResult(
                success=True,  # 没有对应的事件处理插槽不算失败
                outputs={
                    "event_triggered": False,
                    "event_name": event_name
                }
            )
            
        # 获取对应的事件插槽
        slot = self.slots[event_name]
        
        # 设置插槽的上下文
        if self.context:
            slot.set_context(self.context)
            
            # 保存事件数据到上下文
            if event_data:
                for key, value in event_data.items():
                    self.context.set_variable(self.module_id, f"event_{key}", value)
                
        # 执行插槽
        result = await slot.execute()
        
        return ModuleExecutionResult(
            success=result.success,
            outputs={
                "event_triggered": True,
                "event_name": event_name
            },
            child_results={event_name: [result]}
        )
        
    def validate(self) -> bool:
        """验证组合模块配置是否有效"""
        if not super().validate():
            return False
            
        # 验证所有普通子模块
        for module in self.modules:
            if not module.validate():
                return False
                
        # 验证所有事件插槽
        for slot_name, slot in self.slots.items():
            if not slot.validate():
                return False
                
        return True
        
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行组合模块
        
        组合模块的执行过程是按照顺序执行普通子模块，事件插槽则通过事件触发执行。
        """
        modules_results = []
        success = True
        
        # 按照顺序执行普通子模块
        for module in self.modules:
            # 设置模块的上下文
            child_context = self._create_child_context(module, self.context)
            module.set_context(child_context)
            
            # 执行模块
            result = await module.execute()
            modules_results.append(result)
            
            # 如果模块执行失败且需要中断，则停止执行后续模块
            if not result.success:
                success = False
                if result.error and getattr(result, 'stop_on_error', True):
                    logging.error("result.error")
                    break

        # 收集需要输出的变量
        outputs = {}
        if success and modules_results and self.outputs and self.outputs.outputDefs:
            # 创建输出定义名称集合,用于快速查找
            output_names = {output_def.name for output_def in self.outputs.outputDefs}
            # 遍历执行结果
            for result in modules_results:
                # 检查结果中的输出是否在输出定义中
                for output_name, output_value in result.outputs.items():
                    if output_name in output_names:
                        outputs[output_name] = output_value

        return ModuleExecutionResult(
            success=success,
            outputs=outputs,
            child_results={"modules": modules_results}
        ) 