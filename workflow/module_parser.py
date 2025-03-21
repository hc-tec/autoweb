import json
from typing import Dict, Any, Type, Optional
from .module import (
    Module, AtomicModule, CompositeModule, SlotModule,
    EventTriggerModule, PythonCodeModule, ModuleMeta, ModuleType
)
from .module_port import (
    ModuleInputs, ModuleOutputs, InputDefinition, OutputDefinition,
    InputParameter, ValueType, PortValue, ValueContent, ValueSourceType,
    ReferenceValue, InputHelper
)


class ModuleParseError(Exception):
    """模块解析错误"""
    pass


class ModuleParser:
    """模块解析器，用于将JSON配置解析成模块实例"""
    
    # 模块类型映射
    MODULE_TYPE_MAP = {
        ModuleType.ATOMIC: AtomicModule,
        ModuleType.COMPOSITE: CompositeModule,
        ModuleType.SLOT: SlotModule
    }
    
    # 值类型映射
    VALUE_TYPE_MAP = {
        "string": ValueType.STRING,
        "integer": ValueType.INTEGER,
        "float": ValueType.FLOAT,
        "boolean": ValueType.BOOLEAN,
        "object": ValueType.OBJECT,
        "array": ValueType.ARRAY,
        "any": ValueType.ANY
    }
    
    # 自定义模块类型映射
    CUSTOM_MODULE_MAP = {}
    
    @classmethod
    def register_module_type(cls, module_type_name: str, module_class: Type[Module]):
        """
        注册自定义模块类型
        
        Args:
            module_type_name: 模块类型名称
            module_class: 模块类
        """
        cls.CUSTOM_MODULE_MAP[module_type_name] = module_class
        
    @classmethod
    def get_module_class(cls, module_type: str) -> Optional[Type[Module]]:
        """
        获取模块类
        
        Args:
            module_type: 模块类型
            
        Returns:
            模块类
        """
        # 先检查内置模块类型
        if module_type in cls.MODULE_TYPE_MAP:
            return cls.MODULE_TYPE_MAP[module_type]
            
        # 再检查自定义模块类型
        return cls.CUSTOM_MODULE_MAP.get(module_type)
    
    @classmethod
    def parse_module(cls, json_data: Dict[str, Any]) -> Module:
        """解析模块配置
        
        Args:
            json_data: 模块JSON配置
            
        Returns:
            解析后的模块实例
            
        Raises:
            ModuleParseError: 解析错误
        """
        try:
            # 获取基本信息
            module_id = json_data.get("module_id")
            module_type = json_data.get("module_type")
            
            if not module_id or not module_type:
                raise ModuleParseError("Missing module_id or module_type")
                
            # 创建模块实例
            if module_type == ModuleType.ATOMIC and "event_config" in json_data:
                # 特殊处理事件触发模块
                module = cls._create_event_trigger_module(module_id, json_data)
            elif module_type == ModuleType.ATOMIC and "python_code" in json_data:
                # 如果有python_code字段，创建Python代码模块
                module = cls._create_python_code_module(module_id, json_data)
            else:
                module_class = cls.get_module_class(module_type)
                if not module_class:
                    raise ModuleParseError(f"Unknown module type: {module_type}")
                module = module_class(module_id)
        
            # 解析元数据
            if "meta" in json_data:
                meta = cls._parse_meta(json_data["meta"])
                module.set_meta(meta)
                
            # 解析输入定义
            if "inputs" in json_data:
                inputs = cls._parse_module_inputs(json_data["inputs"])
                module.set_inputs(inputs)
                
            # 解析输出定义
            if "outputs" in json_data:
                outputs = cls._parse_module_outputs(json_data["outputs"])
                module.set_outputs(outputs)
                
            # 如果是组合模块，解析子模块和插槽
            if isinstance(module, CompositeModule):
                # 解析子模块
                if "modules" in json_data:
                    for child_data in json_data["modules"]:
                        child_module = cls.parse_module(child_data)
                        module.add_module(child_module)
                        
                # 解析插槽
                if "slots" in json_data:
                    for slot_name, slot_data in json_data["slots"].items():
                        slot = module.add_slot(
                            slot_name,
                            slot_data.get("description", "")
                        )
                        # 解析插槽中的模块
                        if "modules" in slot_data:
                            for slot_module_data in slot_data["modules"]:
                                slot_module = cls.parse_module(slot_module_data)
                                slot.add_module(slot_module)
                                
            return module
            
        except Exception as e:
            raise ModuleParseError(f"Failed to parse module: {str(e)}")
    
    @classmethod
    def _parse_meta(cls, meta_data: Dict[str, Any]) -> ModuleMeta:
        """解析模块元数据"""
        return ModuleMeta(
            title=meta_data.get("title", ""),
            description=meta_data.get("description", ""),
            subtitle=meta_data.get("subtitle"),
            icon=meta_data.get("icon"),
            category=meta_data.get("category"),
            tags=meta_data.get("tags", []),
            version=meta_data.get("version", "1.0.0"),
            author=meta_data.get("author"),
            documentation=meta_data.get("documentation")
        )
    
    @classmethod
    def _parse_module_inputs(cls, inputs_data: Dict[str, Any]) -> ModuleInputs:
        """解析模块输入定义"""
        input_defs = []
        input_parameters = []
        
        # 解析输入定义
        if "input_defs" in inputs_data:
            for def_data in inputs_data["input_defs"]:
                input_def = InputDefinition(
                    name=def_data["name"],
                    type=cls.VALUE_TYPE_MAP[def_data["type"]],
                    description=def_data.get("description", ""),
                    required=def_data.get("required", False),
                    defaultValue=def_data.get("defaultValue")
                )
                input_defs.append(input_def)
                
        # 解析输入参数
        if "input_parameters" in inputs_data:
            for param_data in inputs_data["input_parameters"]:
                param = InputParameter(
                    name=param_data["name"],
                    input=cls._parse_port_value(param_data["input"])
                )
                input_parameters.append(param)
                
        return ModuleInputs(
            inputDefs=input_defs,
            inputParameters=input_parameters,
            settingOnError=inputs_data.get("setting_on_error"),
            apiParam=inputs_data.get("api_param")
        )
    
    @classmethod
    def _parse_module_outputs(cls, outputs_data: Dict[str, Any]) -> ModuleOutputs:
        """解析模块输出定义"""
        output_defs = []
        
        if "output_defs" in outputs_data:
            for def_data in outputs_data["output_defs"]:
                output_def = OutputDefinition(
                    name=def_data["name"],
                    type=cls.VALUE_TYPE_MAP[def_data["type"]],
                    description=def_data.get("description", "")
                )
                output_defs.append(output_def)
                
        return ModuleOutputs(outputDefs=output_defs)
    
    @classmethod
    def _parse_port_value(cls, value_data: Dict[str, Any]) -> PortValue:
        """解析端口值"""
        value_type = cls.VALUE_TYPE_MAP[value_data["type"]]
        value_source_type = ValueSourceType(value_data["value"]["type"])
        
        if value_source_type == ValueSourceType.LITERAL:
            content = value_data["value"]["content"]
        elif value_source_type == ValueSourceType.REF:
            ref_data = value_data["value"]["content"]
            content = ReferenceValue(
                moduleID=ref_data["moduleID"],
                name=ref_data["name"],
                source=ref_data.get("source", "block-output")
            )
        else:
            raise ModuleParseError(f"Unknown value source type: {value_source_type}")
            
        return PortValue(
            type=value_type,
            value=ValueContent(
                content=content,
                type=value_source_type
            )
        )
    
    @classmethod
    def _create_event_trigger_module(cls, module_id: str, json_data: Dict[str, Any]) -> EventTriggerModule:
        """创建事件触发模块"""
        event_config = json_data["event_config"]
        return EventTriggerModule(
            module_id=module_id,
            event_name=event_config["event_name"],
            event_data=event_config.get("event_data", {})
        )
    
    @classmethod
    def _create_python_code_module(cls, module_id: str, json_data: Dict[str, Any]) -> PythonCodeModule:
        """创建Python代码模块"""
        python_code = json_data["python_code"]
        code = python_code.get("code", "")
        description = python_code.get("description", "")
        
        module = PythonCodeModule(module_id)
        if code:
            module.set_code(code, description)
        
        return module
    
    @classmethod
    def load_from_file(cls, file_path: str) -> Module:
        """从文件加载模块配置
        
        Args:
            file_path: JSON配置文件路径
            
        Returns:
            解析后的模块实例
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        return cls.parse_module(json_data)
    
    @classmethod
    def load_from_string(cls, json_string: str) -> Module:
        """从JSON字符串加载模块配置
        
        Args:
            json_string: JSON配置字符串
            
        Returns:
            解析后的模块实例
        """
        json_data = json.loads(json_string)
        return cls.parse_module(json_data) 