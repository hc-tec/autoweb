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
    
    # 预设的格式化器
    FORMAT_DICT = "dict"     # 转换为字典格式 {"field1": "value1", "field2": "value2"}
    FORMAT_LIST = "list"     # 转换为值列表 ["value1", "value2"]
    FORMAT_ORIGINAL = "original"  # 保持原始格式 [{"name": "field1", "value": "value1"}, ...]
    FORMAT_CUSTOM = "custom"      # 自定义格式化器
    
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
        self.format_type = self.FORMAT_DICT  # 默认使用原始格式
        self.custom_formatter_code = None  # 自定义格式化代码
            
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
                required=True
            ),
            InputDefinition(
                name="format_type",
                type=ValueType.STRING,
                description=f"结果格式化类型: {self.FORMAT_ORIGINAL}, {self.FORMAT_DICT}, {self.FORMAT_LIST}, {self.FORMAT_CUSTOM}",
                required=False
            ),
            InputDefinition(
                name="custom_formatter_code",
                type=ValueType.STRING,
                description="自定义格式化代码，需包含一个名为'format_result'的函数",
                required=False
            )
        ]
        
        # ExtractDataBlock 的输出定义
        output_defs = [
            OutputDefinition(
                name="results",
                type=ValueType.ANY,
                description="格式化后的数据结果"
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
            
        # 设置格式化类型
        if "format_type" in args:
            self.format_type = args["format_type"]
            
        # 设置自定义格式化代码
        if "custom_formatter_code" in args:
            self.custom_formatter_code = args["custom_formatter_code"]
        
        return params
    
    def _format_result(self, results: List[Dict[str, Any]]) -> Any:
        """格式化结果
        
        根据format_type选择适当的格式化方法
        
        Args:
            results: 原始结果列表
            
        Returns:
            格式化后的结果
        """
        try:
            if self.format_type == self.FORMAT_DICT:
                # 转换为字典格式
                return {item["name"]: item["value"] for item in results}
                
            elif self.format_type == self.FORMAT_LIST:
                # 转换为值列表
                return [item["value"] for item in results]
                
            elif self.format_type == self.FORMAT_CUSTOM and self.custom_formatter_code:
                # 执行自定义格式化代码
                return self._execute_custom_formatter(results)
                
            else:
                # 默认保持原始格式
                return results
                
        except Exception as e:
            logging.error(f"格式化结果失败: {str(e)}")
            # 出错时返回原始结果
            return results
    
    def _execute_custom_formatter(self, results: List[Dict[str, Any]]) -> Any:
        """执行自定义格式化代码
        
        执行用户提供的Python代码来格式化结果
        
        Args:
            results: 原始结果列表
            
        Returns:
            格式化后的结果
        """
        if not self.custom_formatter_code:
            return results
            
        try:
            # 创建本地环境
            local_vars = {"results": results}
            
            # 编译并执行代码
            exec(self.custom_formatter_code, {}, local_vars)
            
            # 检查是否定义了format_result函数
            if "format_result" not in local_vars or not callable(local_vars["format_result"]):
                logging.error("自定义格式化代码中未找到format_result函数")
                return results
                
            # 调用format_result函数
            return local_vars["format_result"](results)
            
        except Exception as e:
            logging.error(f"执行自定义格式化代码失败: {str(e)}")
            return results
    
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
        
    async def _execute_internal(self) -> ModuleExecutionResult:
        """执行Block逻辑，并处理结果格式化"""
        # 调用父类方法执行Block
        result = await super()._execute_internal()
        
        # 如果执行成功，处理结果格式化
        if result.success and result.outputs and "results" in result.outputs:
            try:
                # 保存原始结果
                raw_results = result.outputs["results"]
                
                # 格式化结果
                formatted_results = self._format_result(raw_results)
                
                # 更新输出
                result.outputs["results"] = formatted_results
                result.outputs["raw_results"] = raw_results
                
            except Exception as e:
                logging.error(f"处理结果格式化失败: {str(e)}")
                # 保持原始输出不变
                
        return result
