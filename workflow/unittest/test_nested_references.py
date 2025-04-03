import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import json
import unittest
from workflow.module import Module, ModuleType, AtomicModule
from workflow.module_port import (
    ValueType, ValueSourceType, PortValue, ValueContent,
    ReferenceValue, InputHelper, ModuleInputs, ModuleOutputs,
    InputDefinition, OutputDefinition
)
from workflow.module_context import ModuleContext
from workflow.module_parser import ModuleParser


class TestNestedReferences(unittest.TestCase):
    """测试嵌套引用解析功能"""
    
    def setUp(self):
        """测试前准备"""
        # 创建一个源模块，作为引用的来源
        self.source_module = AtomicModule("source-module")
        
        # 设置输出定义
        outputs = ModuleOutputs(
            outputDefs=[
                OutputDefinition(name="items", type=ValueType.ARRAY, description="测试数组"),
                OutputDefinition(name="user", type=ValueType.OBJECT, description="测试对象")
            ]
        )
        self.source_module.set_outputs(outputs)
        
        # 创建一个消费模块，它会引用源模块的输出
        self.target_module = AtomicModule("target-module")
        
        # 设置输入定义
        inputs = ModuleInputs(
            inputDefs=[
                InputDefinition(name="item_name", type=ValueType.STRING, description="数组中项目的名称"),
                InputDefinition(name="user_id", type=ValueType.STRING, description="用户ID")
            ],
            inputParameters=[]
        )
        self.target_module.set_inputs(inputs)
        
        # 创建模块上下文并设置给模块
        self.context = ModuleContext()
        self.context.enter_scope("root")  # 创建一个根作用域
        
        # 设置源模块的输出值
        test_items = [
            {"id": 1, "name": "Item 1", "tags": ["tag1", "tag2"]},
            {"id": 2, "name": "Item 2", "tags": ["tag2", "tag3"]}
        ]
        test_user = {
            "id": "user123",
            "profile": {
                "name": "Test User",
                "email": "test@example.com",
                "settings": {
                    "theme": "dark",
                    "notifications": True
                }
            },
            "roles": ["user", "admin"]
        }
        
        # 设置变量到上下文
        self.context.set_variable(self.source_module.module_id, "items", test_items)
        self.context.set_variable(self.source_module.module_id, "user", test_user)
    
    def test_property_access(self):
        """测试通过property属性访问引用值的字段"""
        # 创建对用户ID的引用，使用property访问
        user_id_ref = ReferenceValue(
            moduleID=self.source_module.module_id,
            name="user",
            property="id"
        )
        
        # 创建端口值
        port_value = PortValue(
            type=ValueType.STRING,
            value=ValueContent(
                content=user_id_ref,
                type=ValueSourceType.REF
            )
        )
        
        # 解析引用
        resolved_value = self.context.resolve_port_value(port_value)
        
        # 验证结果
        self.assertEqual(resolved_value, "user123")
    
    def test_path_access(self):
        """测试通过path路径访问嵌套属性"""
        # 创建对用户邮箱的引用，使用path访问
        email_ref = ReferenceValue(
            moduleID=self.source_module.module_id,
            name="user",
            path="profile.email"
        )
        
        # 创建端口值
        port_value = PortValue(
            type=ValueType.STRING,
            value=ValueContent(
                content=email_ref,
                type=ValueSourceType.REF
            )
        )
        
        # 解析引用
        resolved_value = self.context.resolve_port_value(port_value)
        
        # 验证结果
        self.assertEqual(resolved_value, "test@example.com")
    
    def test_array_index_access(self):
        """测试通过数组索引访问元素"""
        # 创建对数组中第一个项目名称的引用
        item_name_ref = ReferenceValue(
            moduleID=self.source_module.module_id,
            name="items",
            path="[0].name"
        )
        
        # 创建端口值
        port_value = PortValue(
            type=ValueType.STRING,
            value=ValueContent(
                content=item_name_ref,
                type=ValueSourceType.REF
            )
        )
        
        # 解析引用
        resolved_value = self.context.resolve_port_value(port_value)
        
        # 验证结果
        self.assertEqual(resolved_value, "Item 1")
    
    def test_complex_path(self):
        """测试复杂路径表达式"""
        # 创建对复杂嵌套属性的引用
        theme_ref = ReferenceValue(
            moduleID=self.source_module.module_id,
            name="user",
            path="profile.settings.theme"
        )
        
        # 创建端口值
        port_value = PortValue(
            type=ValueType.STRING,
            value=ValueContent(
                content=theme_ref,
                type=ValueSourceType.REF
            )
        )
        
        # 解析引用
        resolved_value = self.context.resolve_port_value(port_value)
        
        # 验证结果
        self.assertEqual(resolved_value, "dark")
    
    def test_combined_property_and_path(self):
        """测试同时使用property和path"""
        # 创建同时使用property和path的引用
        roles_ref = ReferenceValue(
            moduleID=self.source_module.module_id,
            name="user",
            property="roles",  # 先获取roles属性
            path="[1]"         # 然后获取数组中的第二个元素
        )
        
        # 创建端口值
        port_value = PortValue(
            type=ValueType.STRING,
            value=ValueContent(
                content=roles_ref,
                type=ValueSourceType.REF
            )
        )
        
        # 解析引用
        resolved_value = self.context.resolve_port_value(port_value)
        
        # 验证结果
        self.assertEqual(resolved_value, "admin")
    
    def test_nested_array_access(self):
        """测试嵌套数组访问"""
        # 创建对嵌套数组元素的引用
        tag_ref = ReferenceValue(
            moduleID=self.source_module.module_id,
            name="items",
            path="[1].tags[0]"  # 第二个项目的第一个标签
        )
        
        # 创建端口值
        port_value = PortValue(
            type=ValueType.STRING,
            value=ValueContent(
                content=tag_ref,
                type=ValueSourceType.REF
            )
        )
        
        # 解析引用
        resolved_value = self.context.resolve_port_value(port_value)
        
        # 验证结果
        self.assertEqual(resolved_value, "tag2")
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试不存在的属性
        invalid_ref = ReferenceValue(
            moduleID=self.source_module.module_id,
            name="user",
            path="profile.nonexistent"
        )
        
        # 创建端口值
        port_value = PortValue(
            type=ValueType.STRING,
            value=ValueContent(
                content=invalid_ref,
                type=ValueSourceType.REF
            )
        )
        
        # 验证解析引用时抛出适当的异常
        with self.assertRaises(ValueError):
            self.context.resolve_port_value(port_value)
    
    def test_from_json_config(self):
        """测试从JSON配置解析引用"""
        # 创建包含嵌套引用的JSON配置
        json_config = {
            "module_id": "test-module",
            "module_type": "atomic",
            "inputs": {
                "input_defs": [
                    {
                        "name": "user_email",
                        "type": "string",
                        "description": "用户邮箱"
                    }
                ],
                "input_parameters": [
                    {
                        "name": "user_email",
                        "input": {
                            "type": "string",
                            "value": {
                                "type": "reference",
                                "content": {
                                    "moduleID": self.source_module.module_id,
                                    "name": "user",
                                    "path": "profile.email"
                                }
                            }
                        }
                    }
                ]
            }
        }
        
        # 解析模块
        module = ModuleParser.parse_module(json_config)
        
        # 验证输入参数被正确解析
        email_param = module.inputs.inputParameters[0]
        self.assertEqual(email_param.name, "user_email")
        
        # 解析引用值
        ref_value = email_param.input.value.content
        self.assertEqual(ref_value.moduleID, self.source_module.module_id)
        self.assertEqual(ref_value.name, "user")
        self.assertEqual(ref_value.path, "profile.email")
        
        # 测试引用解析
        module.set_context(self.context)  # 设置上下文
        
        # 手动解析引用值
        port_value = email_param.input
        resolved_value = self.context.resolve_port_value(port_value)
        
        # 验证解析结果
        self.assertEqual(resolved_value, "test@example.com")


if __name__ == "__main__":
    unittest.main() 