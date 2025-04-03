"""基础模块类

包含Module基类、ModuleType枚举和ModuleMeta数据类，这些是所有模块类型的基础组件。
"""

from typing import Dict, List, Optional, Any, Callable, Set, Union
from dataclasses import dataclass, field
from ..module_port import ModuleInputs, ModuleOutputs, ReferenceValue, ValueSourceType, InputDefinition, OutputDefinition, ValueType
from ..module_context import ModuleContext, ModuleExecutionResult


@dataclass
class ModuleMeta:
    """模块元数据"""
    title: str  # 模块标题
    description: str  # 模块描述
    subtitle: Optional[str] = None  # 模块副标题
    icon: Optional[str] = None  # 模块图标URL
    category: Optional[str] = None  # 模块分类
    tags: List[str] = field(default_factory=list)  # 模块标签
    version: str = "1.0.0"  # 模块版本
    author: Optional[str] = None  # 模块作者
    documentation: Optional[str] = None  # 模块文档URL


class ModuleType:
    """模块类型"""
    ATOMIC = "atomic"  # 原子模块，有自己的执行逻辑
    COMPOSITE = "composite"  # 组合模块，仅执行子模块
    SLOT_CONTAINER = "slot_container"
    SLOT = "slot"  # 插槽模块，作为特定插入点
    EVENT_TRIGGER = "event_trigger"  # 事件触发模块，用于触发事件
    PYCODE = "python_code"
    LOOP = "loop"  # 循环模块，用于循环执行子模块
    LOOP_BODY = "loop_body"  # 循环体模块，用于定义循环内执行的内容
    WORKFLOW = "workflow"  # 工作流模块
    INPUT_NODE = "DynamicInputNode"
    OUTPUT_NODE = "DynamicOutputNode"


class Module:
    """模块基类"""
    
    def __init__(self, module_id: str, module_type: str = ModuleType.ATOMIC):
        self.module_id = module_id
        self.module_type = module_type
        self.meta: Optional[ModuleMeta] = None
        self.inputs: Optional[ModuleInputs] = None
        self.outputs: Optional[ModuleOutputs] = None
        self.parent: Optional[Module] = None  # 父模块
        self.context: Optional[ModuleContext] = None  # 模块执行上下文
        self.stop_bubble: bool = False  # 是否停止变量冒泡
        
    def set_meta(self, meta: ModuleMeta):
        """设置模块元数据"""
        self.meta = meta
        
    def set_inputs(self, inputs: ModuleInputs):
        """设置模块输入"""
        self.inputs = inputs
        
    def set_outputs(self, outputs: ModuleOutputs):
        """设置模块输出"""
        self.outputs = outputs
        
    def set_context(self, context: ModuleContext):
        """设置模块上下文"""
        self.context = context
        
    def validate(self) -> bool:
        """验证模块配置是否有效"""
        if not self.meta or not self.inputs or not self.outputs:
            return False
        return True
        
    async def execute(self) -> ModuleExecutionResult:
        """执行模块逻辑 - 模板方法
        
        这是一个模板方法，定义了模块执行的通用流程:
        1. 检查上下文是否设置
        2. 进入模块作用域
        3. 调用具体的执行逻辑（由子类实现）
        4. 存储输出到上下文
        5. 将输出导出到父上下文
        6. 确保离开模块作用域
        
        Returns:
            执行结果
        """
        if not self.context:
            return ModuleExecutionResult(
                success=False,
                outputs={},
                error="Context not set"
            )
            
        # 进入模块作用域
        self.context.enter_scope(self.module_id)
        
        try:
            # 解析输入参数并存储到上下文 (如果有)
            self._resolve_inputs()
            
            # 打印模块信息
            if self.meta:
                print(f"模块: {self.meta.title}, 模块ID: {self.module_id}")

            # 调用具体的执行逻辑(由子类实现)
            result = await self._execute_internal()
            
            # 将输出导出到父上下文
            parent_context = self.context.get_parent_context()
            if parent_context and result.success and result.outputs:
                for output_name, output_value in result.outputs.items():
                    parent_context.set_variable(self.module_id, output_name, output_value)
                    
            return result
        finally:
            # 确保离开模块作用域
            self.context.exit_scope()
            
    def _resolve_inputs(self):
        """解析输入参数并存储到上下文
        
        处理各种类型的输入参数，包括嵌套引用结构
        """
        parent_context = self.context.get_parent_context()
        if not parent_context:
            return
            
        if not self.inputs or not self.inputs.inputParameters:
            return
            
        # 收集必需参数名称，用于错误处理
        required_params = set()
        if self.inputs.inputDefs:
            for input_def in self.inputs.inputDefs:
                if input_def.required:
                    required_params.add(input_def.name)
        
        # 处理所有输入参数
        for param in self.inputs.inputParameters:
            try:
                # 根据值类型解析
                if param.input.value.type == ValueSourceType.LITERAL:
                    value = param.input.value.content
                else:
                    # 获取引用值
                    ref_value = param.input.value.content
                    
                    # 尝试使用冒泡方式获取变量
                    if isinstance(ref_value, ReferenceValue):
                        # 首先尝试常规解析方式
                        try:
                            value = parent_context.resolve_port_value(param.input)
                        except:
                            # 如果常规方式失败，尝试使用冒泡方式
                            bubble_value = self.get_module_output(ref_value.moduleID, ref_value.name)
                            if bubble_value is not None:
                                value = bubble_value
                            else:
                                # 两种方式都失败，重新抛出异常
                                raise ValueError(f"无法解析引用: {ref_value.moduleID}.{ref_value.name}")
                    else:
                        # 使用上下文解析引用值
                        value = parent_context.resolve_port_value(param.input)
                    
                # 设置到当前模块的上下文中
                self.context.set_variable(self.module_id, param.name, value)
                
            except Exception as e:
                # 如果是必需参数，则抛出异常
                if param.name in required_params:
                    raise ValueError(f"必需参数 '{param.name}' 解析失败: {str(e)}")
                # 否则仅记录警告
                import logging
                logging.warning(f"模块 {self.module_id}: 参数 '{param.name}' 解析失败: {str(e)}")
            
    async def _execute_internal(self) -> ModuleExecutionResult:
        """实际的执行逻辑，由子类实现"""
        raise NotImplementedError("Module must implement _execute_internal method")
        
    def _create_child_context(self, child_module: "Module", parent_context: ModuleContext) -> ModuleContext:
        """创建子模块上下文
        
        Args:
            child_module: 子模块
            parent_context: 父模块上下文
            
        Returns:
            子模块的上下文
        """
        # 创建新的上下文，并设置父上下文
        child_context = ModuleContext(parent_context=parent_context)
                    
        return child_context
        
    def get_output(self, output_name: str) -> Any:
        """获取指定输出值"""
        if not self.outputs:
            raise ValueError("Module outputs not set")
        
        if not self.context:
            raise ValueError("Module context not set")
            
        return self.context.get_variable(self.module_id, output_name)
    
    def trigger_event(self, event_name: str, event_data: Dict[str, Any] = None) -> Optional[ModuleExecutionResult]:
        """触发事件
        
        在模块执行过程中，可以通过此方法触发父模块中的事件处理插槽。
        """
        # 查找可以处理事件的父模块
        parent = self.parent
        while parent:
            if hasattr(parent, 'trigger_event') and callable(parent.trigger_event):
                return parent.trigger_event(event_name, event_data)
            parent = parent.parent
            
    def export_outputs(self, target_dict: Dict[str, Any] = None) -> Dict[str, Any]:
        """导出模块的输出变量
        
        在模块执行完成后，可以通过此方法将模块的输出变量导出到外部系统或父模块。
        
        Args:
            target_dict: 可选的目标字典，用于存储导出的变量
            
        Returns:
            包含所有输出变量的字典 {output_name: output_value}
        """
        if not self.outputs or not self.outputs.outputDefs:
            return {}
            
        if not self.context:
            raise ValueError("Module context not set")
            
        result = target_dict or {}
        
        # 导出所有已定义的输出
        for output_def in self.outputs.outputDefs:
            try:
                # 获取输出值
                output_value = self.get_output(output_def.name)
                # 存储到结果字典中
                result[output_def.name] = output_value
            except Exception as e:
                print(f"Warning: Failed to export output {output_def.name}: {str(e)}")
                
        return result

    def get_module_output(self, target_module_id: str, output_name: str, bubble: bool = True) -> Any:
        """获取任意模块的输出值，支持变量冒泡
        
        Args:
            target_module_id: 目标模块ID
            output_name: 输出名称
            bubble: 是否启用冒泡机制(向上查找)
            
        Returns:
            目标模块的输出值
            
        Notes:
            如果bubble为True，将按照以下顺序查找变量:
            1. 当前模块上下文
            2. 父模块上下文 (递归向上，除非遇到stop_bubble=True的模块)
        """
        # 首先在当前上下文查找
        if self.context:
            try:
                return self.context.get_variable(target_module_id, output_name)
            except KeyError:
                # 当前上下文未找到，继续查找
                pass
                
        # 如果启用冒泡且有父模块，向上查找
        if bubble and self.parent and not self.stop_bubble:
            return self.parent.get_module_output(target_module_id, output_name, bubble)
                
        # 返回None而不是抛出异常
        return None
        
    def stop_bubble_propagation(self):
        """停止变量冒泡传播"""
        self.stop_bubble = True
        
    def enable_bubble_propagation(self):
        """启用变量冒泡传播"""
        self.stop_bubble = False 