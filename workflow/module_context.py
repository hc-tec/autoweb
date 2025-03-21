from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .module_port import PortValue, ValueSourceType, ReferenceValue


@dataclass
class ModuleExecutionResult:
    """模块执行结果"""
    success: bool
    outputs: Dict[str, Any]
    error: Optional[str] = None
    child_results: Dict[str, List["ModuleExecutionResult"]] = None  # 子模块执行结果，按插槽名称分组


class ContextScope:
    """上下文作用域"""
    
    def __init__(self, module_id: str, parent: Optional["ContextScope"] = None):
        self.module_id = module_id
        self.parent = parent
        self.variables: Dict[str, Dict[str, Any]] = {}  # module_id -> {output_name -> value}
        
    def set_variable(self, module_id: str, output_name: str, value: Any):
        """设置变量值"""
        if module_id not in self.variables:
            self.variables[module_id] = {}
        self.variables[module_id][output_name] = value
        
    def get_variable(self, module_id: str, output_name: str) -> Any:
        """获取变量值"""
        # 先在当前作用域查找
        if module_id in self.variables and output_name in self.variables[module_id]:
            return self.variables[module_id][output_name]
            
        # 如果当前作用域没有，且存在父作用域，则向上查找
        if self.parent:
            return self.parent.get_variable(module_id, output_name)
            
        # 如果没有找到，抛出异常
        raise KeyError(f"Variable {module_id}.{output_name} not found in context")
        
    def create_child_scope(self, module_id: str) -> "ContextScope":
        """创建子作用域"""
        return ContextScope(module_id, self)


class ModuleContext:
    """模块执行上下文管理器"""
    
    def __init__(self, parent_context: Optional["ModuleContext"] = None):
        self._current_scope: Optional[ContextScope] = None
        self._execution_results: Dict[str, ModuleExecutionResult] = {}  # 存储模块执行结果
        self._parent_context = parent_context  # 父上下文
        
    def enter_scope(self, module_id: str):
        """进入模块作用域"""
        if not self._current_scope:
            # 如果是第一个作用域，创建根作用域
            self._current_scope = ContextScope(module_id)
        else:
            # 否则创建子作用域
            self._current_scope = self._current_scope.create_child_scope(module_id)
            
    def exit_scope(self):
        """退出当前作用域"""
        if self._current_scope and self._current_scope.parent:
            self._current_scope = self._current_scope.parent
        else:
            self._current_scope = None
            
    def set_variable(self, module_id: str, output_name: str, value: Any):
        """设置变量值"""
        if not self._current_scope:
            raise RuntimeError("No active context scope")
        self._current_scope.set_variable(module_id, output_name, value)
        
    def get_variable(self, module_id: str, output_name: str) -> Any:
        """获取变量值"""
        if not self._current_scope:
            raise RuntimeError("No active context scope")
        return self._current_scope.get_variable(module_id, output_name)
    
    def get_parent_context(self) -> Optional["ModuleContext"]:
        """获取父上下文"""
        return self._parent_context
    
    def set_parent_context(self, parent_context: Optional["ModuleContext"]):
        """设置父上下文"""
        self._parent_context = parent_context
        
    def set_execution_result(self, module_id: str, result: ModuleExecutionResult):
        """设置模块执行结果"""
        self._execution_results[module_id] = result
        
    def get_execution_result(self, module_id: str) -> Optional[ModuleExecutionResult]:
        """获取模块执行结果"""
        return self._execution_results.get(module_id)
        
    def resolve_port_value(self, port_value: PortValue) -> Any:
        """解析端口值"""
        if port_value.value.type == ValueSourceType.REF:
            ref = port_value.value.content
            if not isinstance(ref, ReferenceValue):
                raise ValueError(f"Invalid reference value: {ref}")
            return self.get_variable(ref.moduleID, ref.name)
        else:
            raise ValueError(f"Unknown value type: {port_value.value.type}")
            
    def create_execution_context(self, parent_variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建执行上下文"""
        context = {}
        if parent_variables:
            context.update(parent_variables)
        return context
        
    def clear(self):
        """清空上下文"""
        self._current_scope = None
        self._execution_results.clear()
