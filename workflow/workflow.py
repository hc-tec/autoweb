from typing import Dict, List, Any, Optional
from .module import Module, ModuleMeta, ModuleSlot
from .module_port import ModuleInputs, ModuleOutputs
from .module_context import ModuleContext, ModuleExecutionResult


class Workflow:
    """工作流"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.modules: Dict[str, Module] = {}  # 所有模块
        self.connections: Dict[str, List[str]] = {}  # 模块连接关系，source_id -> [target_id]
        self.context = ModuleContext()  # 工作流上下文
        self.execution_order: List[str] = []  # 模块执行顺序
        
    def add_module(self, module: Module) -> bool:
        """添加模块"""
        if module.module_id in self.modules:
            return False
        self.modules[module.module_id] = module
        return True
        
    def connect_modules(self, source_id: str, target_id: str) -> bool:
        """连接模块"""
        if source_id not in self.modules or target_id not in self.modules:
            return False
            
        if source_id not in self.connections:
            self.connections[source_id] = []
        
        if target_id not in self.connections[source_id]:
            self.connections[source_id].append(target_id)
            
        return True
        
    def calculate_execution_order(self) -> bool:
        """计算模块执行顺序"""
        # 使用拓扑排序计算模块执行顺序
        visited = set()
        temp = set()
        order = []
        
        def visit(module_id: str) -> bool:
            """访问模块"""
            if module_id in temp:
                # 存在循环依赖
                return False
            if module_id in visited:
                return True
                
            temp.add(module_id)
            
            # 访问所有下游模块
            if module_id in self.connections:
                for target_id in self.connections[module_id]:
                    if not visit(target_id):
                        return False
                        
            temp.remove(module_id)
            visited.add(module_id)
            order.append(module_id)
            return True
            
        # 对所有模块进行拓扑排序
        for module_id in self.modules:
            if module_id not in visited:
                if not visit(module_id):
                    # 存在循环依赖
                    return False
                    
        # 反转顺序，因为我们需要从没有依赖的模块开始执行
        order.reverse()
        self.execution_order = order
        return True
        
    def execute(self) -> Dict[str, ModuleExecutionResult]:
        """执行工作流"""
        if not self.execution_order:
            if not self.calculate_execution_order():
                raise ValueError("Failed to calculate execution order, there might be circular dependencies")
                
        results = {}
        
        # 执行每个模块
        for module_id in self.execution_order:
            module = self.modules[module_id]
            
            # 进入模块作用域
            self.context.enter_scope(module_id)
            
            try:
                # 执行模块
                result = module.execute(lambda: self.context.create_execution_context())
                
                # 存储执行结果
                self.context.set_execution_result(module_id, result)
                results[module_id] = result
                
                # 设置输出变量
                if result.success and result.outputs:
                    for output_name, output_value in result.outputs.items():
                        self.context.set_variable(module_id, output_name, output_value)
            finally:
                # 退出模块作用域
                self.context.exit_scope()
                
        return results
        
    def get_module_by_id(self, module_id: str) -> Optional[Module]:
        """通过ID获取模块"""
        return self.modules.get(module_id)
        
    def clear(self):
        """清空工作流"""
        self.modules.clear()
        self.connections.clear()
        self.context.clear()
        self.execution_order.clear()


# 示例：循环模块
class LoopModule(Module):
    """循环模块"""
    
    def __init__(self, module_id: str):
        super().__init__(module_id)
        
        # 添加循环体插槽
        loop_body_slot = ModuleSlot(
            name="loop_body",
            description="循环体",
            required=True,
            multiple=True
        )
        self.add_slot(loop_body_slot)
        
    def execute(self, context_factory: callable) -> ModuleExecutionResult:
        """执行循环模块"""
        # 创建模块上下文
        context = context_factory()
        self.set_context(context)
        
        # 解析循环次数
        loop_count = 5  # 假设循环5次，实际应从输入参数中获取
        
        outputs = {}
        child_results = {"loop_body": []}
        
        # 执行循环
        for i in range(loop_count):
            # 在每次循环中设置循环变量
            parent_context = {"loop_index": i}
            
            # 执行循环体插槽中的所有模块
            slot_results = self.execute_slot("loop_body", parent_context)
            child_results["loop_body"].extend(slot_results)
            
        return ModuleExecutionResult(
            success=True,
            outputs=outputs,
            child_results=child_results
        )


# 示例：条件模块
class ConditionModule(Module):
    """条件模块"""
    
    def __init__(self, module_id: str):
        super().__init__(module_id)
        
        # 添加条件为真时执行的插槽
        true_slot = ModuleSlot(
            name="true_branch",
            description="条件为真时执行",
            required=False,
            multiple=True
        )
        self.add_slot(true_slot)
        
        # 添加条件为假时执行的插槽
        false_slot = ModuleSlot(
            name="false_branch",
            description="条件为假时执行",
            required=False,
            multiple=True
        )
        self.add_slot(false_slot)
        
    def execute(self, context_factory: callable) -> ModuleExecutionResult:
        """执行条件模块"""
        # 创建模块上下文
        context = context_factory()
        self.set_context(context)
        
        # 解析条件
        condition = True  # 假设条件为真，实际应从输入参数中获取
        
        outputs = {}
        child_results = {}
        
        # 根据条件执行相应的分支
        if condition:
            slot_results = self.execute_slot("true_branch", context)
            child_results["true_branch"] = slot_results
        else:
            slot_results = self.execute_slot("false_branch", context)
            child_results["false_branch"] = slot_results
            
        return ModuleExecutionResult(
            success=True,
            outputs=outputs,
            child_results=child_results
        )
