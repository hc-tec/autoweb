import enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass


class ValueType(enum.Enum):
    """值类型枚举"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    ANY = "any"


class ValueSourceType(enum.Enum):
    """值来源类型枚举"""
    LITERAL = "literal"  # 字面量
    REF = "ref"  # 引用其他模块的输出


@dataclass
class ValueContent:
    """值内容"""
    content: Any
    type: ValueSourceType


@dataclass
class PortValue:
    """端口值"""
    type: ValueType
    value: ValueContent


@dataclass
class InputDefinition:
    """输入定义"""
    name: str
    type: ValueType
    description: str
    required: bool = False
    input: Dict = None  # 保留字段，用于存储其他配置
    defaultValue: Any = None


@dataclass
class InputParameter:
    """输入参数"""
    name: str
    input: PortValue


@dataclass
class OutputDefinition:
    """输出定义"""
    name: str
    type: ValueType
    description: str


@dataclass
class ModuleInputs:
    """模块输入"""
    inputDefs: List[InputDefinition]  # 输入定义
    inputParameters: List[InputParameter]  # 输入参数（实际值）
    settingOnError: Dict = None  # 错误处理设置
    apiParam: List[Dict] = None  # API参数，如果模块是API类型


@dataclass
class ModuleOutputs:
    """模块输出"""
    outputDefs: List[OutputDefinition]  # 输出定义
    

@dataclass
class ReferenceValue:
    """引用值"""
    moduleID: str
    name: str
    source: str = "block-output"  # 默认引用其他模块的输出
    
    
class InputHelper:
    """输入帮助类"""
    
    @staticmethod
    def create_literal_value(value_type: ValueType, content: Any) -> PortValue:
        """创建字面量值"""
        return PortValue(
            type=value_type,
            value=ValueContent(
                content=content,
                type=ValueSourceType.LITERAL
            )
        )
    
    @staticmethod
    def create_reference_value(value_type: ValueType, module_id: str, output_name: str) -> PortValue:
        """创建引用值"""
        ref = ReferenceValue(
            moduleID=module_id,
            name=output_name
        )
        return PortValue(
            type=value_type,
            value=ValueContent(
                content=ref,
                type=ValueSourceType.REF
            )
        )
        
    @staticmethod
    def create_module_output(module_id: str, output_name: str) -> PortValue:
        """创建引用模块输出的值（便捷方法）
        
        自动使用 ANY 类型，适用于简单场景
        """
        return InputHelper.create_reference_value(
            ValueType.ANY,
            module_id,
            output_name
        )
