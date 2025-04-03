from typing import Dict, Any, Optional, List, Type
import asyncio
import inspect
import logging

from workflow.module import AtomicModule, ModuleMeta, ModuleExecutionResult
from workflow.module_port import ModuleInputs, ModuleOutputs, InputDefinition, OutputDefinition, ValueType
from workflow.module_types import Args
from taskflow.task_blocks.block import Block, BlockContext, BlockExecuteParams
from browser.browser_automation import BrowserAutomation


class BlockModuleAdapter(AtomicModule):
    """
    TaskFlow Block 到 Workflow Module 的基本适配器
    将 TaskFlow 的 Block 类适配为 Workflow 的 Module 类
    """
    
    # 全局的浏览器实例，用于在适配器之间共享
    _browser_instance: Optional[BrowserAutomation] = None
    
    # 存储所有已适配的Block类
    BLOCK_CLASS_MAP: Dict[str, Type[Block]] = {}
    
    @classmethod
    def register_block_class(cls, block_name: str, block_class: Type[Block]):
        """注册Block类到适配器映射表"""
        cls.BLOCK_CLASS_MAP[block_name] = block_class
    
    @classmethod
    def get_browser_instance(cls) -> BrowserAutomation:
        """获取或创建共享的浏览器实例"""
        if cls._browser_instance is None:
            cls._browser_instance = BrowserAutomation()
        return cls._browser_instance
    
    @classmethod
    def close_browser(cls):
        """关闭浏览器实例"""
        if cls._browser_instance:
            try:
                cls._browser_instance.browser.quit()
            except:
                pass
            cls._browser_instance = None
    
    def __init__(self, module_id: str, block_type: str, block_name: str = None):
        """
        初始化适配器
        
        Args:
            module_id: 模块ID
            block_type: Block类型
            block_name: Block名称(可选)
        """
        super().__init__(module_id)
        
        # 设置Block信息
        self.block_type = block_type
        self.block_name = block_name or f"{block_type}_{module_id}"
        
        # 获取Block类
        self.block_class = self.BLOCK_CLASS_MAP.get(block_type)
        if not self.block_class:
            raise ValueError(f"未找到Block类型: {block_type}")
            
        # 初始化上下文和Block实例
        self.block_context: BlockContext = None
        self.block_instance: Block = None
        
        # 设置元数据
        self.set_meta(ModuleMeta(
            title=self.block_name,
            description=f"{self.block_type} 的适配器",
            category="taskflow"
        ))

    def _create_block_instance(self, params: Dict[str, Any]) -> Block:
        """创建Block实例"""
        # 创建BlockContext
        self.block_context = BlockContext()
        
        # 设置浏览器实例
        browser = self.get_browser_instance()
        self.block_context.set_browser(browser)

        # 创建Block实例
        return self.block_class({
            "context": self.block_context,
            **params
        })
    
    def _prepare_execute_params(self, args: Dict[str, Any]) -> BlockExecuteParams:
        """准备Block执行参数"""
        params = BlockExecuteParams()
        
        # 设置变量
        for key, value in args.items():
            params.set_variable(key, value)
            
        return params
    
    def get_block_instance_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取Block实例的参数"""
        return {
            "name": self.block_name,
            **params,
        }
    
    def get_input_params(self) -> Dict[str, Any]:
        """获取输入参数
        
        直接从模块上下文中获取已解析的参数值
        
        Returns:
            包含所有输入参数的字典
        """
        input_data = {}
        if self.inputs and self.inputs.inputParameters and self.context:
            for param in self.inputs.inputParameters:
                try:
                    # 直接从上下文中获取已解析的值
                    value = self.context.get_variable(self.module_id, param.name)
                    input_data[param.name] = value
                except Exception as e:
                    logging.error(f"从上下文获取参数失败: {param.name}, 错误: {str(e)}")
        return input_data
    
    # 子类在执行_execute_internal之前无法获取到输入参数，因此添加一个方法，方法子类重写
    def _before_execute(self, block: Block, params: BlockExecuteParams):
        pass
    
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行Block逻辑"""
        try:
            # 准备输入参数
            input_data = self.get_input_params()
            
            # 准备执行参数
            params = self._prepare_execute_params(
                self.get_block_instance_params(input_data)
            )

            # 创建Block实例
            self.block_instance = self._create_block_instance(params.variables)

            # 设置block的输入参数
            for input in self.inputs.inputParameters:
                self.block_instance.add_input_variable(input.name)

            # 设置block的输出参数
            for output in self.outputs.outputDefs:
                self.block_instance.add_output_variable(output.name)

            self._before_execute(self.block_instance, params)
            
            # 执行Block
            self.block_instance.run(params)
            
            # 收集输出结果
            outputs = {}  # 默认结果
            if params.exec_result is not None:
                # 如果Block有明确的执行结果，使用它
                outputs["results"] = params.exec_result
                
            # 添加其他变量作为输出
            for key, value in params.variables.items():
                outputs[key] = value
            
            return ModuleExecutionResult(
                success=True,
                outputs=outputs
            )
            
        except Exception as e:
            return ModuleExecutionResult(
                success=False,
                outputs={},
                error=str(e)
            ) 