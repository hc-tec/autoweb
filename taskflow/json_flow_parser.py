import json
from typing import Optional, List, Any, Dict

from taskflow.control_flow import ControlFlow
from taskflow.field_saver import FieldSaver
from taskflow.task_blocks.block import BlockFactory, Block
from taskflow.data_exporter import ExcelExporter
from taskflow.task_blocks.end_block import EndBlock
from taskflow.variable_system import VariableType, VariableScope


class JsonFlowParser:

    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path

    def parse(self, debug_mode: bool = False) -> ControlFlow:
        data_exporter = ExcelExporter(name='data.xlsx')
        field_saver = FieldSaver()
        field_saver.set_data_exporter(data_exporter)

        control_flow = ControlFlow()
        control_flow.set_field_saver(field_saver)
        if debug_mode:
            control_flow.enable_debug_mode(True)
        
        block_factory = BlockFactory(control_flow.get_context())

        with open(self.json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            
        # 处理全局变量定义
        if "variables" in json_data:
            self.parse_variables(json_data["variables"], control_flow)
            
        # 处理流程块
        json_flow = json_data.get("flow", json_data)
        if not isinstance(json_flow, list):
            json_flow = [json_flow]
            
        self.parse_block(json_flow, None, control_flow, block_factory)

        return control_flow
        
    def parse_variables(self, variables_config: Dict, control_flow: ControlFlow):
        """解析变量配置"""
        context = control_flow.get_context()
        
        for var_name, var_config in variables_config.items():
            var_type_str = var_config.get("type", "string").upper()
            var_value = var_config.get("value", None)
            var_scope_str = var_config.get("scope", "global").upper()
            var_description = var_config.get("description", "")
            var_readonly = var_config.get("readonly", False)
            
            # 解析变量类型
            try:
                var_type = VariableType[var_type_str]
            except KeyError:
                var_type = VariableType.STRING
                
            # 解析变量作用域
            try:
                var_scope = VariableScope[var_scope_str]
            except KeyError:
                var_scope = VariableScope.GLOBAL
                
            # 创建变量
            var = context.create_variable(var_name, var_value, var_type, var_scope)
            
            # 设置变量描述
            if var_description:
                var.set_description(var_description)
                
            # 设置只读属性
            if var_readonly:
                var.set_readonly(True)

    def parse_block(self,
                    json_flow: List[Any],
                    outer_block: Optional[Block],
                    control_flow: ControlFlow,
                    block_factory: BlockFactory):
        last_block: Optional[Block] = None
        for json_config in json_flow:
            block_name = json_config["block"]
            block = block_factory.create_block(block_name, json_config)
            block.load_from_config(control_flow, json_config)
            
            if json_config.get("breakpoint", False):
                block.set_breakpoint(True)

            if "wait_time" in json_config:
                wait_time = float(json_config["wait_time"])
                block.set_wait_time(wait_time)

            if "input_variables" in json_config:
                input_vars = json_config["input_variables"]
                if isinstance(input_vars, list):
                    block.set_input_variables(input_vars)
                else:
                    block.add_input_variable(input_vars)
                    
            if "output_variables" in json_config:
                output_vars = json_config["output_variables"]
                if isinstance(output_vars, list):
                    block.set_output_variables(output_vars)
                else:
                    block.add_output_variable(output_vars)

            if block_name == "StartBlock":
                control_flow.set_start_block(block)
            if block_name == "EndBlock":
                block = block  # type: EndBlock
                block.observe(control_flow.field_saver.save)
            if outer_block:
                outer_block.add_inner(block)
            if last_block:
                last_block.set_next_block(block)
            last_block = block
            if json_config.get("inners", False):
                self.parse_block(json_config["inners"], block, control_flow, block_factory)
