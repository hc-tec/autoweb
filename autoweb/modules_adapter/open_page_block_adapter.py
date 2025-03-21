from typing import Dict, Any
from taskflow.block_context import BlockContext
from workflow.module_context import ModuleExecutionResult
from workflow.module_port import InputDefinition, OutputDefinition, ValueType, ModuleInputs, ModuleOutputs
from taskflow.task_blocks.open_page_block import OpenPageBlock
from taskflow.task_blocks.block import BlockExecuteParams
import logging

from autoweb.modules_adapter.base_adapter import BlockModuleAdapter


class OpenPageBlockAdapter(BlockModuleAdapter):
    """OpenPageBlock 适配器 - 打开网页"""
    
    def __init__(self, module_id: str, block_name: str = None):
        """
        初始化 OpenPageBlock 适配器
        
        Args:
            module_id: 模块ID
            block_name: Block名称(可选)
        """
        # 在使用前，需要先注册 OpenPageBlock 类
        if "OpenPageBlock" not in self.BLOCK_CLASS_MAP:
            self.register_block_class("OpenPageBlock", OpenPageBlock)
            
        # OpenPageBlock 特定属性
        self.page_url = None
        self.fullscreen = False
            
        super().__init__(module_id, "OpenPageBlock", block_name)
        
        # 初始化输入输出定义
        self._initialize_io_definitions()
    
    def _initialize_io_definitions(self):
        """初始化输入输出定义"""
        # OpenPageBlock 的输入定义
        input_defs = [
            InputDefinition(
                name="page_url",
                type=ValueType.STRING,
                description="要打开的页面URL",
                required=True
            ),
            InputDefinition(
                name="fullscreen",
                type=ValueType.BOOLEAN,
                description="是否全屏显示",
                required=False
            )
        ]
        
        # 设置输入输出
        self.set_inputs(ModuleInputs(
            inputDefs=input_defs,
            inputParameters=[]
        ))
        
        self.set_outputs(ModuleOutputs(
            outputDefs=[]
        ))
    
    def _prepare_execute_params(self, args: Dict[str, Any]) -> BlockExecuteParams:
        """准备Block执行参数"""
        params = super()._prepare_execute_params(args)
        
        # 设置属性，这些属性将在创建实例时使用
        if "page_url" in args:
            self.page_url = args["page_url"]
            
        if "fullscreen" in args:
            self.fullscreen = args["fullscreen"]
        
        return params
    
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行Block逻辑"""
        # 执行基类方法
        result = await super()._execute_internal()
        
        # 添加额外的输出信息
        if result.success:
            try:
                browser = self.get_browser_instance()
                current_url = browser.browser.current_url
                result.outputs["current_url"] = current_url
            except Exception as e:
                # 获取URL失败不影响执行结果
                logging.warning(f"获取当前URL失败: {str(e)}")
                
        return result 