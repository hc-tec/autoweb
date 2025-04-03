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
    REF = "reference"  # 引用其他模块的输出


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
    """引用值
    
    表示对另一个模块输出的引用。支持两种引用解析方式：
    1. 常规模式：引用在同一作用域或父作用域中定义的变量
    2. 冒泡模式：如果常规模式无法解析，将沿模块树向上查找变量
    
    Notes:
        冒泡模式只在常规模式失败时启用，可以通过Module.stop_bubble_propagation()
        或ModuleContext.stop_bubble_propagation()来控制冒泡传播
    """
    moduleID: str  # 模块ID
    name: str      # 变量名
    path: Optional[str] = None  # 嵌套路径, 如 "a.b.c" 或 "items[0].name"
    property: Optional[str] = None  # 直接属性名, 如 "id"
    source: str = "block-output"  # 引用来源
    

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

class ReferenceResolver:
    """引用解析器
    
    专门用于处理各种类型的引用解析，针对不同类型采用不同的解析策略，
    支持处理路径表达式和属性访问等高级引用模式
    """
    
    @staticmethod
    def is_reference_object(obj: Any) -> bool:
        """检查对象是否是引用对象"""
        return (isinstance(obj, dict) and 
                "type" in obj and 
                "content" in obj and 
                obj["type"] in ["reference", "ref"])
    
    @staticmethod
    def create_reference_value(ref_data: Dict[str, Any]) -> ReferenceValue:
        """从引用数据创建ReferenceValue对象
        
        支持标准字段(moduleID, name)和扩展字段(path, property)
        """
        return ReferenceValue(
            moduleID=ref_data["moduleID"],
            name=ref_data["name"],
            path=ref_data.get("path"),
            property=ref_data.get("property"),
            source=ref_data.get("source", "block-output")
        )
    
    @classmethod
    def process_reference(cls, ref_data: Any, value_type: ValueType) -> Any:
        """根据值类型处理引用
        
        为不同类型的值选择适当的解析策略
        
        Args:
            ref_data: 引用数据
            value_type: 值类型
            
        Returns:
            处理后的引用结构
        """
        # 根据类型选择不同的处理方法
        if value_type == ValueType.ARRAY:
            return cls._process_array_reference(ref_data)
        elif value_type == ValueType.OBJECT:
            return cls._process_object_reference(ref_data)
        else:
            # 基本类型(String, Integer等)的引用
            return cls._process_basic_reference(ref_data)
    
    @classmethod
    def _process_basic_reference(cls, ref_data: Any) -> ReferenceValue:
        """处理基本类型的引用
        
        对于String, Integer等基本类型，创建引用对象，支持path或property访问
        """
        if isinstance(ref_data, dict) and "moduleID" in ref_data and "name" in ref_data:
            return cls.create_reference_value(ref_data)
        else:
            raise ValueError(f"无效的基本类型引用数据: {ref_data}")
    
    @classmethod
    def _process_array_reference(cls, ref_data: Any) -> Union[ReferenceValue, List]:
        """处理数组类型的引用
        
        数组可能是包含引用的列表，也可能是单个引用指向一个数组，
        或者是一个引用+path组合指向数组中的一个元素
        """
        # 单个引用指向一个数组
        if isinstance(ref_data, dict) and "moduleID" in ref_data and "name" in ref_data:
            return cls.create_reference_value(ref_data)
            
        # 列表形式的引用数据，处理数组内的每个元素
        if isinstance(ref_data, list):
            return [cls._process_element_in_array(item) for item in ref_data]
            
        raise ValueError(f"无效的数组引用数据: {ref_data}")
    
    @classmethod
    def _process_element_in_array(cls, element: Any) -> Any:
        """处理数组中的元素
        
        数组中的元素可以是简单值、引用或包含嵌套引用的对象
        """
        # 如果元素本身是引用
        if cls.is_reference_object(element):
            return cls._process_basic_reference(element["content"])
            
        # 如果元素是对象，需要递归处理其中的引用
        if isinstance(element, dict):
            result = {}
            for key, value in element.items():
                if cls.is_reference_object(value):
                    # 字段值是引用
                    result[key] = cls._process_basic_reference(value["content"])
                else:
                    # 字段值不是引用
                    result[key] = value
            return result
            
        # 简单值直接返回
        return element
    
    @classmethod
    def _process_object_reference(cls, ref_data: Any) -> Union[ReferenceValue, Dict]:
        """处理对象类型的引用
        
        对象可能是包含引用字段的字典，也可能是单个引用指向一个对象，
        或者是一个引用+property组合指向对象的一个属性
        """
        # 如果是单个引用，则处理可能的path或property
        if isinstance(ref_data, dict) and "moduleID" in ref_data and "name" in ref_data:
            return cls.create_reference_value(ref_data)
            
        # 如果是包含引用字段的字典，处理每个字段
        if isinstance(ref_data, dict):
            result = {}
            for key, value in ref_data.items():
                if cls.is_reference_object(value):
                    result[key] = cls._process_basic_reference(value["content"])
                else:
                    result[key] = value
            return result
            
        raise ValueError(f"无效的对象引用数据: {ref_data}")
