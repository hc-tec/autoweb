from typing import Any, Dict, Optional, Set
from enum import Enum
import logging


class VariableType(Enum):
    """变量类型枚举"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    OBJECT = "object"


class VariableScope(Enum):
    """变量作用域枚举"""
    GLOBAL = "global"  # 全局变量
    LOCAL = "local"    # 局部变量
    TEMP = "temp"      # 临时变量


class Variable:
    """变量类"""
    def __init__(self, name: str, value: Any, var_type: VariableType, scope: VariableScope = VariableScope.LOCAL):
        self.name = name
        self.value = value
        self.type = var_type
        self.scope = scope
        self.dependencies: Set[str] = set()  # 依赖的其他变量名
        self.dependents: Set[str] = set()     # 依赖此变量的其他变量名
        self.is_readonly = False
        self.description = ""
        
    def set_value(self, value: Any) -> bool:
        """设置变量值，返回是否设置成功"""
        if self.is_readonly:
            logging.warning(f"尝试修改只读变量 {self.name}")
            return False
        self.value = value
        return True
        
    def get_value(self) -> Any:
        """获取变量值"""
        return self.value
        
    def add_dependency(self, var_name: str):
        """添加依赖"""
        self.dependencies.add(var_name)
        
    def add_dependent(self, var_name: str):
        """添加被依赖"""
        self.dependents.add(var_name)
        
    def remove_dependency(self, var_name: str):
        """移除依赖"""
        self.dependencies.discard(var_name)
        
    def remove_dependent(self, var_name: str):
        """移除被依赖"""
        self.dependents.discard(var_name)
        
    def set_readonly(self, readonly: bool):
        """设置只读状态"""
        self.is_readonly = readonly
        
    def set_description(self, description: str):
        """设置变量描述"""
        self.description = description


class VariableManager:
    """变量管理器"""
    def __init__(self):
        self.variables: Dict[str, Variable] = {}
        self.scope_stack: list[Set[str]] = []  # 作用域栈，用于管理局部变量
        
    def create_variable(self, name: str, value: Any, var_type: VariableType, 
                       scope: VariableScope = VariableScope.LOCAL) -> Variable:
        """创建新变量"""
        if name in self.variables:
            logging.warning(f"变量 {name} 已存在，将被覆盖")
            
        var = Variable(name, value, var_type, scope)
        self.variables[name] = var
        
        if scope == VariableScope.LOCAL and self.scope_stack:
            self.scope_stack[-1].add(name)
            
        return var
        
    def get_variable(self, name: str) -> Optional[Variable]:
        """获取变量"""
        return self.variables.get(name)
        
    def set_variable_value(self, name: str, value: Any) -> bool:
        """设置变量值"""
        var = self.get_variable(name)
        if var:
            return var.set_value(value)
        return False
        
    def get_variable_value(self, name: str) -> Any:
        """获取变量值"""
        var = self.get_variable(name)
        return var.get_value() if var else None
        
    def push_scope(self):
        """创建新的作用域"""
        self.scope_stack.append(set())
        
    def pop_scope(self):
        """弹出当前作用域，并清理其中的局部变量"""
        if self.scope_stack:
            current_scope = self.scope_stack.pop()
            for var_name in current_scope:
                if var_name in self.variables:
                    del self.variables[var_name]
                    
    def add_dependency(self, var_name: str, depends_on: str):
        """添加变量依赖关系"""
        var = self.get_variable(var_name)
        dep_var = self.get_variable(depends_on)
        if var and dep_var:
            var.add_dependency(depends_on)
            dep_var.add_dependent(var_name)
            
    def remove_dependency(self, var_name: str, depends_on: str):
        """移除变量依赖关系"""
        var = self.get_variable(var_name)
        dep_var = self.get_variable(depends_on)
        if var and dep_var:
            var.remove_dependency(depends_on)
            dep_var.remove_dependent(var_name)
            
    def get_dependencies(self, var_name: str) -> Set[str]:
        """获取变量的所有依赖"""
        var = self.get_variable(var_name)
        return var.dependencies if var else set()
        
    def get_dependents(self, var_name: str) -> Set[str]:
        """获取变量的所有被依赖"""
        var = self.get_variable(var_name)
        return var.dependents if var else set()
        
    def set_readonly(self, var_name: str, readonly: bool):
        """设置变量只读状态"""
        var = self.get_variable(var_name)
        if var:
            var.set_readonly(readonly)
            
    def set_description(self, var_name: str, description: str):
        """设置变量描述"""
        var = self.get_variable(var_name)
        if var:
            var.set_description(description)
            
    def clear(self):
        """清空所有变量"""
        self.variables.clear()
        self.scope_stack.clear() 