import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import unittest
import json
from workflow.module_parser import ModuleParser
from workflow.module_context import ModuleContext
from workflow.module_port import ReferenceValue


class TestComplexReferences(unittest.TestCase):
    """测试复杂引用结构的解析"""
    
    def test_nested_array_references(self):
        """测试嵌套数组引用的解析"""
        # 创建测试数据
        json_data = {
            "module_id": "test_module",
            "module_type": "atomic",
            "meta": {
                "title": "测试模块",
                "description": "测试复杂引用结构"
            },
            "inputs": {
                "input_defs": [
                    {
                        "name": "fields",
                        "type": "array",
                        "description": "测试字段",
                        "required": 1
                    }
                ],
                "input_parameters": [
                    {
                        "name": "fields",
                        "input": {
                            "type": "array",
                            "value": {
                                "type": "reference",
                                "content": [
                                    {
                                        "name": "field1",
                                        "xpath": {
                                            "type": "reference",
                                            "content": {
                                                "moduleID": "source_module",
                                                "name": "xpath1"
                                            }
                                        }
                                    },
                                    {
                                        "name": "field2",
                                        "xpath": {
                                            "type": "reference",
                                            "content": {
                                                "moduleID": "source_module",
                                                "name": "xpath2"
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                ]
            },
            "outputs": {
                "output_defs": []
            }
        }
        
        # 解析模块
        module = ModuleParser.parse_module(json_data)
        
        # 验证输入参数的解析
        self.assertIsNotNone(module.inputs)
        self.assertEqual(len(module.inputs.inputParameters), 1)
        
        # 获取字段参数
        fields_param = module.inputs.inputParameters[0]
        self.assertEqual(fields_param.name, "fields")
        
        # 验证引用内容的结构
        ref_content = fields_param.input.value.content
        self.assertIsInstance(ref_content, list)
        self.assertEqual(len(ref_content), 2)
        
        # 验证嵌套引用
        for item in ref_content:
            self.assertIn("name", item)
            self.assertIn("xpath", item)
            self.assertIsInstance(item["xpath"], ReferenceValue)
            self.assertEqual(item["xpath"].moduleID, "source_module")
            
        # 创建上下文并设置模拟数据
        context = ModuleContext()
        parent_context = ModuleContext()
        context.set_parent_context(parent_context)
        parent_context.enter_scope(module.module_id)
        # 在父上下文中设置引用的值
        parent_context.set_variable("source_module", "xpath1", "/html/div[1]")
        parent_context.set_variable("source_module", "xpath2", "/html/div[2]")
        
        # 设置模块上下文
        module.set_context(context)
        
        context.enter_scope("source_module")

        # 解析输入参数
        module._resolve_inputs()
        
        # 验证解析结果
        fields = context.get_variable(module.module_id, "fields")
        self.assertIsInstance(fields, list)
        self.assertEqual(len(fields), 2)
        
        self.assertEqual(fields[0]["name"], "field1")
        self.assertEqual(fields[0]["xpath"], "/html/div[1]")
        
        self.assertEqual(fields[1]["name"], "field2")
        self.assertEqual(fields[1]["xpath"], "/html/div[2]")
        
    def test_extract_data_fields_references(self):
        """测试ExtractDataBlock模块的fields参数引用解析"""
        # 创建测试数据，模拟ExtractDataBlock的fields引用
        json_data = {
            "module_id": "extract_data_module",
            "module_type": "atomic",
            "meta": {
                "title": "提取数据模块",
                "description": "测试字段引用"
            },
            "inputs": {
                "input_defs": [
                    {
                        "name": "fields",
                        "type": "array",
                        "description": "要提取的字段",
                        "required": 1
                    }
                ],
                "input_parameters": [
                    {
                        "name": "fields",
                        "input": {
                            "type": "array",
                            "value": {
                                "type": "reference",
                                "content": [
                                    {
                                        "name": "field1",
                                        "xpath": {
                                            "type": "reference",
                                            "content": {
                                                "moduleID": "source_module",
                                                "name": "xpath1"
                                            }
                                        },
                                        "type": "string"
                                    },
                                    {
                                        "name": "field2",
                                        "xpath": {
                                            "type": "reference",
                                            "content": {
                                                "moduleID": "source_module",
                                                "name": "xpath2"
                                            }
                                        },
                                        "type": "string"
                                    },
                                    {
                                        "name": "field3",
                                        "xpath": {
                                            "type": "reference",
                                            "content": {
                                                "moduleID": "source_module",
                                                "name": "xpath3"
                                            }
                                        },
                                        "type": "string"
                                    }
                                ]
                            }
                        }
                    }
                ]
            },
            "outputs": {
                "output_defs": []
            }
        }
        
        # 解析模块
        module = ModuleParser.parse_module(json_data)
        
        # 验证输入参数
        self.assertIsNotNone(module.inputs)
        self.assertEqual(len(module.inputs.inputParameters), 1)
        
        # 验证fields参数
        fields_param = module.inputs.inputParameters[0]
        self.assertEqual(fields_param.name, "fields")
        self.assertEqual(fields_param.input.type.value, "array")
        
        # 验证fields中的引用内容
        fields = fields_param.input.value.content
        self.assertIsInstance(fields, list)
        self.assertEqual(len(fields), 3)
        
        # 验证每个字段中的xpath引用
        field_names = []
        xpath_refs = []
        for field in fields:
            field_names.append(field["name"])
            self.assertIn("xpath", field)
            self.assertIsInstance(field["xpath"], ReferenceValue)
            xpath_refs.append((field["xpath"].moduleID, field["xpath"].name))
        
        # 验证字段名称
        self.assertEqual(field_names, ["field1", "field2", "field3"])
        
        # 验证xpath引用
        expected_refs = [
            ("source_module", "xpath1"),
            ("source_module", "xpath2"),
            ("source_module", "xpath3")
        ]
        self.assertEqual(xpath_refs, expected_refs)
        
        # 测试解析运行时
        context = ModuleContext()
        parent_context = ModuleContext()
        context.set_parent_context(parent_context)
        # 设置模块上下文并解析输入
        module.set_context(context)
        parent_context.enter_scope(module.module_id)
        # 设置源模块的xpath值
        parent_context.set_variable("source_module", "xpath1", "//div[@class='item1']")
        parent_context.set_variable("source_module", "xpath2", "//div[@class='item2']")
        parent_context.set_variable("source_module", "xpath3", "//div[@class='item3']")
        
        context.enter_scope("source_module")
        module._resolve_inputs()
        
        # 验证解析结果
        result_fields = context.get_variable(module.module_id, "fields")
        self.assertIsInstance(result_fields, list)
        self.assertEqual(len(result_fields), 3)
        
        # 验证解析后的字段
        self.assertEqual(result_fields[0]["name"], "field1")
        self.assertEqual(result_fields[0]["xpath"], "//div[@class='item1']")
        self.assertEqual(result_fields[0]["type"], "string")
        
        self.assertEqual(result_fields[1]["name"], "field2")
        self.assertEqual(result_fields[1]["xpath"], "//div[@class='item2']")
        self.assertEqual(result_fields[1]["type"], "string")
        
        self.assertEqual(result_fields[2]["name"], "field3")
        self.assertEqual(result_fields[2]["xpath"], "//div[@class='item3']")
        self.assertEqual(result_fields[2]["type"], "string")


if __name__ == "__main__":
    unittest.main() 