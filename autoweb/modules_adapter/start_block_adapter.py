from workflow.module_port import InputDefinition, OutputDefinition, ValueType, ModuleInputs, ModuleOutputs
from taskflow.task_blocks.start_block import StartBlock
from taskflow.task_blocks.block import BlockExecuteParams
from workflow.module_context import ModuleExecutionResult

from autoweb.modules_adapter.base_adapter import BlockModuleAdapter


class StartBlockAdapter(BlockModuleAdapter):
    """StartBlock 适配器 - 工作流的起点"""
    
    def __init__(self, module_id: str, block_name: str = None):
        """
        初始化 StartBlock 适配器
        
        Args:
            module_id: 模块ID
            block_name: Block名称(可选)
        """
        # 在使用前，需要先注册 StartBlock 类
        if "StartBlock" not in self.BLOCK_CLASS_MAP:
            self.register_block_class("StartBlock", StartBlock)
            
        super().__init__(module_id, "StartBlock", block_name)
        
        # 初始化输入输出定义
        self._initialize_io_definitions()
    
    def _initialize_io_definitions(self):
        """初始化输入输出定义"""
        # StartBlock 没有特定的输入参数
        input_defs = []
        
        # 设置输入输出
        self.set_inputs(ModuleInputs(
            inputDefs=input_defs,
            inputParameters=[]
        ))
        
        self.set_outputs(ModuleOutputs(
            outputDefs=[]
        ))
    
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行Block逻辑"""
        # 执行基类方法
        result = await super()._execute_internal()
        return result 