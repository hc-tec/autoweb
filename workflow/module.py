from typing import Dict, List, Optional, Any, Callable, Set, Union
from dataclasses import dataclass, field
from .module_port import ModuleInputs, ModuleOutputs
from .module_context import ModuleContext, ModuleExecutionResult
from .module_types import Args, Output, CodeFunction
import asyncio

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
    SLOT = "slot"  # 插槽模块，作为特定插入点


class SlotType:
    """插槽类型"""
    NORMAL = "normal"  # 普通插槽，用于组合模块
    EVENT = "event"    # 事件插槽，用于响应事件


@dataclass
class ModuleSlot:
    """模块插槽定义"""
    name: str  # 插槽名称
    description: str  # 插槽描述
    required: bool = False  # 是否必须填充
    multiple: bool = False  # 是否允许多个模块
    slot_type: str = SlotType.NORMAL  # 插槽类型
    modules: List["Module"] = field(default_factory=list)  # 插入的模块列表


@dataclass
class EventData:
    """事件数据"""
    event_name: str  # 事件名称
    source_module_id: str  # 触发事件的模块ID
    data: Dict[str, Any] = field(default_factory=dict)  # 事件携带的数据


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
        
    def execute(self) -> ModuleExecutionResult:
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
            
            # 调用具体的执行逻辑(由子类实现)
            result = self._execute_internal()
            
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
        """解析输入参数并存储到上下文"""
        parent_context = self.context.get_parent_context()
        if parent_context and self.inputs and self.inputs.inputParameters:
            for param in self.inputs.inputParameters:
                try:
                    value = parent_context.resolve_port_value(param.input)
                    self.context.set_variable(self.module_id, param.name, value)
                except Exception as e:
                    print(f"Warning: Failed to resolve input parameter {param.name}: {str(e)}")
            
    def _execute_internal(self) -> ModuleExecutionResult:
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
        
        # 仅传递子模块需要的参数
        # if child_module.inputs and child_module.inputs.inputParameters:
        #     for param in child_module.inputs.inputParameters:
        #         # 解析输入参数的值
        #         try:
        #             value = parent_context.resolve_port_value(param.input)
        #             # 将解析后的值设置到子模块上下文中
        #             child_context.set_variable(child_module.module_id, param.name, value)
        #         except Exception as e:
        #             # 如果解析失败，记录错误但继续处理其他参数
        #             print(f"Warning: Failed to resolve input parameter {param.name}: {str(e)}")
                    
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
            if isinstance(parent, CompositeModule):
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


class AtomicModule(Module):
    """原子模块
    
    原子模块是直接实现业务逻辑的模块，如Python代码模块、接口调用模块等。
    """
    
    def __init__(self, module_id: str):
        super().__init__(module_id, ModuleType.ATOMIC)
        
    def _execute_internal(self) -> ModuleExecutionResult:
        """执行模块逻辑
        
        原子模块需要重写此方法，实现具体的业务逻辑
        """
        return ModuleExecutionResult(
            success=True,
            outputs={},
            error=None
        )


class SlotModule(Module):
    """插槽模块
    
    插槽模块作为组合模块中的特定插入点，可以包含一系列子模块。
    当组合模块执行到插槽模块时，会依次执行插槽中的所有子模块。
    """
    
    def __init__(self, module_id: str, slot_name: str, description: str = ""):
        super().__init__(module_id, ModuleType.SLOT)
        self.slot_name = slot_name
        self.description = description
        self.modules: List[Module] = []  # 插槽中的模块列表
        
        # 设置元数据
        meta = ModuleMeta(
            title=f"插槽: {slot_name}",
            description=description or f"插槽 {slot_name}",
            category="slot"
        )
        self.set_meta(meta)
        
        # 设置默认的空输入输出
        self.set_inputs(ModuleInputs(inputDefs=[], inputParameters=[]))
        self.set_outputs(ModuleOutputs(outputDefs=[]))
        
    def add_module(self, module: Module) -> bool:
        """添加模块到插槽"""
        module.parent = self
        self.modules.append(module)
        return True
        
    def _execute_internal(self) -> ModuleExecutionResult:
        """执行插槽中的所有模块"""
        child_results = []
        
        # 依次执行插槽中的所有模块
        for module in self.modules:
            # 为每个子模块设置同样的上下文
            module.set_context(self.context)
            
            # 执行子模块
            result = module.execute()
            child_results.append(result)
            
            # 如果子模块执行失败且需要中断，则停止执行后续模块
            if not result.success and result.error and getattr(result, 'stop_on_error', False):
                break
                
        success = all(result.success for result in child_results)
        
        return ModuleExecutionResult(
            success=success,
            outputs={},  # 插槽本身不产生输出
            child_results={self.slot_name: child_results}
        )


class CompositeModule(Module):
    """组合模块
    
    组合模块作为容器，包含普通子模块和事件插槽。
    普通子模块按顺序执行，而事件插槽在触发时执行。
    """
    
    def __init__(self, module_id: str):
        super().__init__(module_id, ModuleType.COMPOSITE)
        self.slots: Dict[str, SlotModule] = {}  # 事件插槽字典
        self.modules: List[Module] = []  # 普通子模块列表
        
    def add_module(self, module: Module) -> bool:
        """添加普通子模块"""
        module.parent = self
        self.modules.append(module)
        return True
        
    def add_slot(self, slot_name: str, description: str = "") -> SlotModule:
        """添加事件插槽"""
        slot_id = f"{self.module_id}_slot_{slot_name}"
        slot = SlotModule(slot_id, slot_name, description)
        slot.parent = self
        self.slots[slot_name] = slot
        return slot
        
    def get_slot(self, slot_name: str) -> Optional[SlotModule]:
        """获取指定名称的事件插槽"""
        return self.slots.get(slot_name)
        
    def add_module_to_slot(self, slot_name: str, module: Module) -> bool:
        """向指定事件插槽添加模块"""
        slot = self.get_slot(slot_name)
        if not slot:
            slot = self.add_slot(slot_name)
        return slot.add_module(module)
        
    def trigger_event(self, event_name: str, event_data: Dict[str, Any] = None) -> ModuleExecutionResult:
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
        result = slot.execute()
        
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
        
    def _execute_internal(self) -> ModuleExecutionResult:
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
            result = module.execute()
            modules_results.append(result)
            
            # 如果模块执行失败且需要中断，则停止执行后续模块
            if not result.success:
                success = False
                if result.error and getattr(result, 'stop_on_error', False):
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


class EventTriggerModule(AtomicModule):
    """事件触发模块
    
    事件触发模块用于触发特定事件，当执行到此模块时，会触发父模块中对应名称的事件。
    """
    
    def __init__(self, module_id: str, event_name: str, event_data: Dict[str, Any] = None):
        super().__init__(module_id)
        self.event_name = event_name
        self.event_data = event_data or {}
        
        # 设置元数据
        meta = ModuleMeta(
            title=f"触发事件: {event_name}",
            description=f"触发 {event_name} 事件",
            category="event"
        )
        self.set_meta(meta)
        
        # 设置默认的空输入输出
        self.set_inputs(ModuleInputs(inputDefs=[], inputParameters=[]))
        self.set_outputs(ModuleOutputs(outputDefs=[]))
        
    def set_event_data(self, event_data: Dict[str, Any]):
        """设置事件数据"""
        self.event_data = event_data
        
    def _execute_internal(self) -> ModuleExecutionResult:
        """执行事件触发逻辑"""
        # 首先从上下文中解析事件数据
        event_data = {}
        if self.inputs and self.inputs.inputParameters:
            for param in self.inputs.inputParameters:
                try:
                    value = self.context.get_variable(self.module_id, param.name)
                    event_data[param.name] = value
                except Exception as e:
                    print(f"Warning: Failed to get event data parameter {param.name}: {str(e)}")
        
        # 合并静态事件数据和动态解析的事件数据
        merged_event_data = {**self.event_data, **event_data}
        
        # 查找父模块并触发事件
        parent = self.parent
        while parent:
            if isinstance(parent, CompositeModule):
                # 调用父模块的事件触发方法
                result = parent.trigger_event(self.event_name, merged_event_data)
                
                # 记录事件触发结果
                return ModuleExecutionResult(
                    success=result.success,
                    outputs={
                        "event_triggered": result.outputs.get("event_triggered", False),
                        "event_name": self.event_name
                    },
                    child_results=result.child_results
                )
                
            # 向上查找父模块
            parent = parent.parent
            
        # 未找到可触发事件的父模块
        return ModuleExecutionResult(
            success=True,  # 未找到事件插槽不算失败
            outputs={
                "event_triggered": False,
                "event_name": self.event_name
            }
        )


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
            if self.inputs and self.inputs.inputParameters:
                for param in self.inputs.inputParameters:
                    try:
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
            if self.code_function.is_async:
                result = await main_func(args)
            else:
                result = main_func(args)
                
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
