from typing import Optional, Any, Set

from browser.browser_automation import BrowserAutomation
from taskflow.variable_system import Variable, VariableManager, VariableScope, VariableType


class BlockContext:
    def __init__(self):
        self.browser: Optional[BrowserAutomation] = None
        self._debug_mode = False  # 调试模式标志
        self.variable_manager = VariableManager()  # 变量管理器

    def set_browser(self, browser: BrowserAutomation):
        self.browser = browser
        return self

    def set_debug_mode(self, debug_mode: bool):
        """设置调试模式开关"""
        self._debug_mode = debug_mode
        return self

    def is_debug_mode(self) -> bool:
        """获取当前调试模式状态"""
        return self._debug_mode

    def create_variable(self, name: str, value: Any, var_type: VariableType, 
                       scope: VariableScope = VariableScope.LOCAL):
        """创建新变量"""
        return self.variable_manager.create_variable(name, value, var_type, scope)

    def get_variable(self, name: str) -> Optional[Variable]:
        """获取变量"""
        return self.variable_manager.get_variable(name)

    def set_variable_value(self, name: str, value: Any) -> bool:
        """设置变量值"""
        return self.variable_manager.set_variable_value(name, value)

    def get_variable_value(self, name: str) -> Any:
        """获取变量值"""
        return self.variable_manager.get_variable_value(name)

    def set_readonly(self, var_name: str, readonly: bool):
        """设置变量只读状态"""
        self.variable_manager.set_readonly(var_name, readonly)

    def set_description(self, var_name: str, description: str):
        """设置变量描述"""
        self.variable_manager.set_description(var_name, description)

    def clear_variables(self):
        """清空所有变量"""
        self.variable_manager.clear()









