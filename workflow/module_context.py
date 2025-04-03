from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .module_port import PortValue, ValueSourceType, ReferenceValue, ValueType


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
        self._stop_bubble = False  # 是否停止变量冒泡
        
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
        """解析端口值
        
        根据端口值的类型和来源类型进行解析，支持复杂嵌套引用
        
        Args:
            port_value: 端口值
            
        Returns:
            解析后的实际值
        """
        # 获取值类型和来源类型
        value_type = port_value.type
        source_type = port_value.value.type
        
        # 根据来源类型处理
        if source_type == ValueSourceType.LITERAL:
            # 字面量值直接返回
            return port_value.value.content
            
        elif source_type == ValueSourceType.REF:
            # 引用值需要根据类型进行解析
            ref_value = port_value.value.content
            return self._resolve_reference_value(ref_value, value_type)
            
        else:
            raise ValueError(f"不支持的值来源类型: {source_type.value}")
    
    def _resolve_reference_value(self, ref_value: Any, value_type: ValueType) -> Any:
        """解析引用值
        
        根据值类型选择合适的解析策略，支持通过path或property访问嵌套属性
        
        Args:
            ref_value: 引用值
            value_type: 值类型
            
        Returns:
            解析后的实际值
        """
        # 根据引用值的类型和值类型进行解析
        if isinstance(ref_value, ReferenceValue):
            # 先获取基本引用值
            base_value = self._resolve_simple_reference(ref_value)
            
            # 处理嵌套访问(如path或property)
            return self._resolve_nested_access(base_value, ref_value)
            
        elif isinstance(ref_value, list) and value_type == ValueType.ARRAY:
            # 处理数组中的每个元素
            return self._resolve_array_elements(ref_value)
            
        elif isinstance(ref_value, dict) and value_type == ValueType.OBJECT:
            # 处理对象中的每个字段
            return self._resolve_object_fields(ref_value)
            
        else:
            # 其他情况，可能是结构与类型不匹配
            raise ValueError(f"引用值结构 {type(ref_value).__name__} 与类型 {value_type.value} 不匹配")
    
    def _resolve_nested_access(self, base_value: Any, ref: ReferenceValue) -> Any:
        """解析嵌套访问
        
        处理通过path或property访问对象的嵌套属性
        
        Args:
            base_value: 基础值
            ref: 引用值对象，包含path或property等信息
            
        Returns:
            访问嵌套属性后的值
        """
        result = base_value
        
        # 处理property直接属性访问
        # if ref.property and isinstance(result, dict):
        #     if ref.property in result:
        #         result = result[ref.property]
        #     else:
        #         raise KeyError(f"属性 '{ref.property}' 在对象中不存在")
                
        # 处理path路径访问 (如 "items[0].name")
        if ref.path:
            result = self._navigate_object_path(result, ref.path)
            
        return result
    
    def _navigate_object_path(self, obj: Any, path: str) -> Any:
        """导航对象路径
        
        沿着路径表达式访问嵌套对象的属性
        支持点号访问(obj.prop)和数组索引访问(obj[0])
        
        Args:
            obj: 要导航的对象
            path: 路径表达式
            
        Returns:
            访问路径后的值
        """
        # 没有路径时直接返回对象
        if not path:
            return obj
            
        # 分割路径，支持点号(.)和数组索引([])
        import re
        # 匹配属性名或数组索引
        parts = re.findall(r'(\w+)|\[(\d+)\]', path)
        current = obj
        
        for part in parts[1:]:
            prop_name, index = part
            
            if prop_name:  # 属性访问
                if isinstance(current, dict) and prop_name in current:
                    current = current[prop_name]
                elif hasattr(current, prop_name):
                    current = getattr(current, prop_name)
                else:
                    raise ValueError(f"属性 '{prop_name}' 在对象中不存在")
                    
            elif index:  # 数组索引访问
                idx = int(index)
                if isinstance(current, (list, tuple)) and 0 <= idx < len(current):
                    current = current[idx]
                else:
                    raise ValueError(f"索引 {idx} 超出数组范围或对象不是数组")
                    
        return current
        
    def _resolve_simple_reference(self, ref: ReferenceValue) -> Any:
        """解析简单引用"""
        return self.get_variable(ref.moduleID, ref.name)
        
    def _resolve_array_elements(self, elements: List) -> List:
        """解析数组中的元素"""
        result = []
        for item in elements:
            if isinstance(item, ReferenceValue):
                # 元素是引用
                result.append(self._resolve_simple_reference(item))
            elif isinstance(item, dict):
                # 元素是对象，需要处理其中的引用字段
                resolved_item = {}
                for key, value in item.items():
                    if isinstance(value, ReferenceValue):
                        resolved_item[key] = self._resolve_simple_reference(value)
                    elif isinstance(value, dict) and value.get("type") == "literal":
                        resolved_item[key] = value.get("content")
                    else:
                        resolved_item[key] = value
                result.append(resolved_item)
            else:
                # 元素是基本类型
                result.append(item)
        return result
        
    def _resolve_object_fields(self, obj: Dict) -> Dict:
        """解析对象中的字段"""
        result = {}
        for key, value in obj.items():
            if isinstance(value, ReferenceValue):
                # 字段值是引用
                result[key] = self._resolve_simple_reference(value)
            elif isinstance(value, (list, dict)):
                # 字段值是复杂结构，需要递归处理
                if isinstance(value, list):
                    result[key] = self._resolve_array_elements(value)
                else:
                    result[key] = self._resolve_object_fields(value)
            else:
                # 字段值是基本类型
                result[key] = value
        return result
            
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

    def get_module_output(self, module_id: str, output_name: str, bubble: bool = True) -> Any:
        """获取指定模块的输出值，支持冒泡机制
        
        Args:
            module_id: 模块ID
            output_name: 输出名称
            bubble: 是否启用冒泡机制(向上查找)
            
        Returns:
            模块输出值，未找到时返回None
            
        Notes:
            如果bubble为True，将按照以下顺序查找变量:
            1. 当前作用域
            2. 父上下文 (除非_stop_bubble=True)
        """
        try:
            # 先在当前作用域查找
            if self._current_scope:
                return self._current_scope.get_variable(module_id, output_name)
        except KeyError:
            pass
            
        # 如果启用冒泡且有父上下文，向上查找
        if bubble and self._parent_context and not self._stop_bubble:
            return self._parent_context.get_module_output(module_id, output_name, bubble)
            
        # 未找到返回None
        return None
        
    def stop_bubble_propagation(self):
        """停止变量冒泡传播"""
        self._stop_bubble = True
        
    def enable_bubble_propagation(self):
        """启用变量冒泡传播"""
        self._stop_bubble = False
