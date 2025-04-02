from typing import Dict, List, Optional, Any, Callable, Set, Union
from dataclasses import dataclass, field
from .module_port import ModuleInputs, ModuleOutputs, ValueSourceType, InputDefinition, OutputDefinition, ValueType
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
    SLOT_CONTAINER = "slot_container"
    SLOT = "slot"  # 插槽模块，作为特定插入点
    EVENT_TRIGGER = "event_trigger"  # 事件触发模块，用于触发事件
    PYCODE = "python_code"
    LOOP = "loop"  # 循环模块，用于循环执行子模块
    LOOP_BODY = "loop_body"  # 循环体模块，用于定义循环内执行的内容


@dataclass
class ModuleSlot:
    """模块插槽定义"""
    name: str  # 插槽名称
    description: str  # 插槽描述
    required: bool = False  # 是否必须填充
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
        
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行模块逻辑
        
        原子模块需要重写此方法，实现具体的业务逻辑
        """
        return ModuleExecutionResult(
            success=True,
            outputs={},
            error=None
        )


# SlotContainer is belong to CompositeModule
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
        
    def add_slot(self, slot_name: str, description: str = ""):
        """添加事件插槽"""
        slot = SlotModule(slot_name)
        slot.parent = self
        self.slots[slot_name] = slot
        return slot
        
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



class SlotModule(CompositeModule):
    """插槽模块
    
    插槽模块作为组合模块中的特定插入点，可以包含一系列子模块。
    当组合模块执行到插槽模块时，会依次执行插槽中的所有子模块。
    """
    
    def __init__(self, module_id: str):
        super().__init__(module_id, ModuleType.SLOT)


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
        
    async def _execute_internal(self) -> ModuleExecutionResult:
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
                result = await parent.trigger_event(self.event_name, merged_event_data)
                
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
            # if self.code_function.is_async:
            result = await main_func(args)
            # else:
            #     result = main_func(args)
                
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


class LoopModule(CompositeModule):
    """循环模块
    
    循环模块接收一个数组作为输入，并基于数组的长度进行循环。
    在每次循环中，循环模块会将当前的索引和元素传递给循环体。
    """
    
    def __init__(self, module_id: str):
        super().__init__(module_id, ModuleType.LOOP)
        self.loop_array = []  # 循环数组
        self.loop_body_slot_name = "loop_body"
        # 设置默认的输入输出定义
        self.create_default_config()
        
    def create_default_config(self):
        """创建默认的配置"""
        # 设置输入定义
        input_defs = [
            InputDefinition(
                name="array",
                type=ValueType.ARRAY,
                description="要循环的数组",
                required=True
            ),
            InputDefinition(
                name="continue_on_error",
                type=ValueType.BOOLEAN,
                description="循环体执行失败时是否继续",
                required=False,
                defaultValue=True
            )
        ]
        
        # 设置输出定义
        output_defs = [
            OutputDefinition(
                name="iterations",
                type=ValueType.INTEGER,
                description="循环次数"
            ),
            OutputDefinition(
                name="results",
                type=ValueType.ARRAY,
                description="所有成功迭代的结果数组"
            )
        ]
        
        # 设置输入输出
        self.set_inputs(ModuleInputs(inputDefs=input_defs, inputParameters=[]))
        self.set_outputs(ModuleOutputs(outputDefs=output_defs))
        
        # 设置元数据
        self.set_meta(ModuleMeta(
            title="循环模块",
            description="基于数组执行循环操作",
            category="control",
            tags=["loop", "iteration", "control-flow"]
        ))
        
    def get_loop_body_slot(self) -> Optional[Module]:
        """获取循环体插槽"""
        return self.slots.get(self.loop_body_slot_name)
        
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行循环模块
        
        循环执行插槽中的模块，并在每次循环中传递当前的索引和元素。
        """
        # 获取循环数组
        try:
            # 尝试从上下文中获取数组参数
            self.loop_array = self.context.get_variable(self.module_id, "array")
            if not isinstance(self.loop_array, list):
                return ModuleExecutionResult(
                    success=False,
                    outputs={},
                    error=f"输入参数 'array' 不是有效的数组"
                )
        except Exception as e:
            return ModuleExecutionResult(
                success=False,
                outputs={},
                error=f"无法获取输入数组: {str(e)}"
            )
        
        # 获取错误处理选项
        try:
            continue_on_error = self.context.get_variable(self.module_id, "continue_on_error")
        except:
            # 默认为True
            continue_on_error = True
            
        # 获取循环体插槽
        loop_body = self.get_loop_body_slot()
        if not loop_body:
            return ModuleExecutionResult(
                success=False,
                outputs={},
                error="循环体插槽未定义"
            )
            
        # 存储循环结果
        loop_results = []
        all_success = True
        
        # 遍历数组执行循环
        for index, item in enumerate(self.loop_array):
            # 创建新的循环上下文
            loop_context = self._create_child_context(loop_body, self.context)
            
            # 设置循环索引和元素到上下文
            self.context.set_variable(self.module_id, "index", index)
            self.context.set_variable(self.module_id, "item", item)
            
            # 为循环体设置上下文
            loop_body.set_context(loop_context)
            
            # 执行循环体
            result = await loop_body.execute()
            loop_results.append(result)
            
            # 如果循环体执行失败，根据设置决定是否继续
            if not result.success:
                all_success = False
                if not continue_on_error:
                    break
        
        # 收集所有循环体的输出
        combined_outputs = {
            "iterations": len(self.loop_array),
            "results": [result.outputs for result in loop_results if result.success]
        }
        
        return ModuleExecutionResult(
            success=all_success,
            outputs=combined_outputs,
            child_results={"loop_iterations": loop_results}
        )
