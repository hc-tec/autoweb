from typing import Dict, Any, List
from workflow.module_context import ModuleExecutionResult
from workflow.module_port import InputDefinition, OutputDefinition, ValueType, ModuleInputs, ModuleOutputs
from taskflow.task_blocks.extract_data_block import ExtractDataBlock, Field, TextFieldExtractor
from taskflow.task_blocks.block import Block, BlockExecuteParams
from taskflow.data_exporter import ExcelExporter
from taskflow.field_saver import FieldSaver
import logging

from autoweb.modules_adapter.base_adapter import BlockModuleAdapter


class ExtractDataBlockAdapter(BlockModuleAdapter):
    """ExtractDataBlock 适配器 - 从页面提取数据"""
    
    def __init__(self, module_id: str, block_name: str = None):
        """
        初始化 ExtractDataBlock 适配器
        
        Args:
            module_id: 模块ID
            block_name: Block名称(可选)
        """
        # 在使用前，需要先注册 ExtractDataBlock 类
        if "ExtractDataBlock" not in self.BLOCK_CLASS_MAP:
            self.register_block_class("ExtractDataBlock", ExtractDataBlock)
            
        # ExtractDataBlock 特定属性
        self.fields = []  # 提取的字段列表
        self.use_relative_xpath = False  # 是否使用相对XPath
        self.export_to_excel = False  # 是否导出到Excel
        self.field_saver = None  # 数据保存器
            
        super().__init__(module_id, "ExtractDataBlock", block_name)
        
        # 初始化输入输出定义
        self._initialize_io_definitions()
    
    def _initialize_io_definitions(self):
        """初始化输入输出定义"""
        # ExtractDataBlock 的输入定义
        input_defs = [
            InputDefinition(
                name="fields",
                type=ValueType.ARRAY,
                description="要提取的字段定义",
                required=True
            ),
            InputDefinition(
                name="use_relative_xpath",
                type=ValueType.BOOLEAN,
                description="是否使用相对XPath",
                required=False
            ),
            InputDefinition(
                name="export_to_excel",
                type=ValueType.BOOLEAN,
                description="是否导出到Excel",
                required=False
            )
        ]
        
        # ExtractDataBlock 的输出定义
        output_defs = [
            OutputDefinition(
                name="data",
                type=ValueType.ARRAY,
                description="提取的数据结果"
            ),
            OutputDefinition(
                name="result_count",
                type=ValueType.INTEGER,
                description="提取的数据数量"
            )
        ]
        
        # 设置输入输出
        self.set_inputs(ModuleInputs(
            inputDefs=input_defs,
            inputParameters=[]
        ))
        
        self.set_outputs(ModuleOutputs(
            outputDefs=output_defs
        ))
    
    def _prepare_execute_params(self, args: Dict[str, Any]) -> BlockExecuteParams:
        """准备Block执行参数"""
        params = super()._prepare_execute_params(args)
        
        # 设置属性
        if "fields" in args:
            self.fields = args["fields"]
            
        if "use_relative_xpath" in args:
            self.use_relative_xpath = args["use_relative_xpath"]
            
        if "export_to_excel" in args:
            self.export_to_excel = args["export_to_excel"]
        
        return params
    
    def _configure_block_instance(self, block: ExtractDataBlock):
        """配置Block实例"""
        # 设置是否使用相对XPath
        if hasattr(self, "use_relative_xpath"):
            block.set_use_relative_xpath(self.use_relative_xpath)
            
        # 设置字段
        self._add_fields_to_block(block)
        
        # 设置数据导出
        if self.export_to_excel:
            data_exporter = ExcelExporter(name=f"{self.block_name}_data.xlsx")
            self.field_saver = FieldSaver()
            self.field_saver.set_data_exporter(data_exporter)
            block.set_field_observer(self.field_saver)
    
    def _add_fields_to_block(self, block: ExtractDataBlock):
        """将字段添加到Block实例"""
        if not self.fields:
            return
            
        field_list = []
        for field_def in block.fields:
            field_name = field_def.get("name")
            field_xpath = field_def.get("xpath")
            field_extractor_type = field_def.get("extractor_type", "TextFieldExtractor")
            
            if field_name and field_xpath:
                field = Field(field_name, field_xpath)
                
                # 设置提取器
                if field_extractor_type == "TextFieldExtractor":
                    field.set_extractor(TextFieldExtractor(f"{field_name}提取器"))
                
                field_list.append(field)
                
        if field_list:
            block.add_field_list(field_list)

    def _before_execute(self, block: Block, params: BlockExecuteParams):
        # 先配置Block实例
        self._configure_block_instance(block)
