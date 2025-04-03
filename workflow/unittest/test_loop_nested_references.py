import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import json
import unittest
from workflow.module import Module, ModuleType, AtomicModule, LoopModule
from workflow.module_port import (
    ValueType, ValueSourceType, PortValue, ValueContent,
    ReferenceValue, InputHelper, ModuleInputs, ModuleOutputs,
    InputDefinition, OutputDefinition, InputParameter
)
from workflow.module_context import ModuleContext
from workflow.module_parser import ModuleParser


class TestLoopNestedReferences(unittest.TestCase):
    """测试循环模块中的嵌套引用解析功能"""
    
    def setUp(self):
        """测试前准备"""
        # 创建一个数据源模块，提供循环数据
        self.data_source = AtomicModule("data-source")
        
        # 设置输出定义
        data_source_outputs = ModuleOutputs(
            outputDefs=[
                OutputDefinition(name="items", type=ValueType.ARRAY, description="循环数据项")
            ]
        )
        self.data_source.set_outputs(data_source_outputs)
        
        # 创建一个循环模块
        self.loop_module = LoopModule("loop-module")
        
        # 配置循环模块的输入，指定使用data-source模块的items作为循环数据
        loop_input_param = InputParameter(
            name="array",
            input=InputHelper.create_reference_value(
                ValueType.ARRAY, 
                "data-source", 
                "items"
            )
        )
        loop_inputs = ModuleInputs(
            inputDefs=[
                InputDefinition(name="array", type=ValueType.ARRAY, description="循环数组", required=True)
            ],
            inputParameters=[loop_input_param]
        )
        self.loop_module.set_inputs(loop_inputs)
        
        # 创建循环体模块作为循环模块的子模块
        self.loop_body = AtomicModule("loop-body")
        
        # 设置循环体的输入和输出
        loop_body_inputs = ModuleInputs(
            inputDefs=[
                InputDefinition(name="item_id", type=ValueType.INTEGER, description="项目ID"),
                InputDefinition(name="item_detail", type=ValueType.STRING, description="项目详情")
            ],
            inputParameters=[]
        )
        loop_body_outputs = ModuleOutputs(
            outputDefs=[
                OutputDefinition(name="processed_item", type=ValueType.OBJECT, description="处理后的项目")
            ]
        )
        self.loop_body.set_inputs(loop_body_inputs)
        self.loop_body.set_outputs(loop_body_outputs)
        
        # 将循环体添加到循环模块的slot中
        self.loop_module.add_module_to_slot("loop_body", self.loop_body)
        
        # 创建结果收集模块
        self.result_collector = AtomicModule("result-collector")
        
        # 设置结果收集模块的输入
        result_collector_inputs = ModuleInputs(
            inputDefs=[
                InputDefinition(name="processed_items", type=ValueType.ARRAY, description="处理后的项目列表"),
                InputDefinition(name="item_count", type=ValueType.INTEGER, description="项目数量")
            ],
            inputParameters=[]
        )
        self.result_collector.set_inputs(result_collector_inputs)
        
        # 创建模块上下文
        self.context = ModuleContext()
        self.context.enter_scope("root")  # 创建根作用域
        
        # 设置测试数据
        test_items = [
            {
                "id": 1,
                "name": "Item 1",
                "details": {
                    "description": "First item description",
                    "category": "Category A",
                    "tags": ["tag1", "tag2"]
                }
            },
            {
                "id": 2,
                "name": "Item 2",
                "details": {
                    "description": "Second item description",
                    "category": "Category B",
                    "tags": ["tag2", "tag3"]
                }
            },
            {
                "id": 3,
                "name": "Item 3",
                "details": {
                    "description": "Third item description",
                    "category": "Category A",
                    "tags": ["tag1", "tag4"]
                }
            }
        ]
        
        # 设置数据源输出到上下文
        self.context.set_variable(self.data_source.module_id, "items", test_items)
    
    def test_loop_item_reference(self):
        """测试循环项中的嵌套引用解析
        
        注意：这个测试方法模拟了LoopModule的执行流程，手动处理循环项
        """
        # 设置循环模块的上下文
        self.loop_module.set_context(self.context)
        
        # 进入循环模块的作用域
        self.context.enter_scope(self.loop_module.module_id)
        
        # 模拟循环过程 - 第一个循环项
        loop_item = {
            "id": 1, 
            "name": "Item 1", 
            "details": {"description": "First item description"}
        }
        
        # 在上下文中设置当前循环项和索引
        self.context.set_variable("current-item", "", loop_item)
        self.context.set_variable(self.loop_module.module_id, "index", 0)
        
        # 创建引用当前循环项的对象
        id_ref = ReferenceValue(
            moduleID="current-item",
            name="",
            path="id"
        )
        
        detail_ref = ReferenceValue(
            moduleID="current-item",
            name="",
            path="details.description"
        )
        
        # 创建端口值
        id_port_value = PortValue(
            type=ValueType.INTEGER,
            value=ValueContent(
                content=id_ref,
                type=ValueSourceType.REF
            )
        )
        
        detail_port_value = PortValue(
            type=ValueType.STRING,
            value=ValueContent(
                content=detail_ref,
                type=ValueSourceType.REF
            )
        )
        
        # 解析引用
        resolved_id = self.context.resolve_port_value(id_port_value)
        resolved_detail = self.context.resolve_port_value(detail_port_value)
        
        # 验证结果
        self.assertEqual(resolved_id, 1)
        self.assertEqual(resolved_detail, "First item description")
        
        # 模拟循环过程 - 第二个循环项
        loop_item = {
            "id": 2, 
            "name": "Item 2", 
            "details": {"description": "Second item description"}
        }
        
        # 更新上下文中的当前循环项和索引
        self.context.set_variable("current-item", "", loop_item)
        self.context.set_variable(self.loop_module.module_id, "index", 1)
        
        # 解析引用
        resolved_id = self.context.resolve_port_value(id_port_value)
        resolved_detail = self.context.resolve_port_value(detail_port_value)
        
        # 验证结果
        self.assertEqual(resolved_id, 2)
        self.assertEqual(resolved_detail, "Second item description")
        
        # 退出循环模块的作用域
        self.context.exit_scope()
    
    def test_nested_array_in_loop(self):
        """测试循环项中嵌套数组的引用解析"""
        # 设置循环模块的上下文
        self.loop_module.set_context(self.context)
        
        # 进入循环模块的作用域
        self.context.enter_scope(self.loop_module.module_id)
        
        # 创建引用循环项中嵌套数组的引用
        tags_ref = ReferenceValue(
            moduleID="current-item",
            name="",
            path="details.tags[1]"  # 访问第二个标签
        )
        
        # 创建端口值
        tags_port_value = PortValue(
            type=ValueType.STRING,
            value=ValueContent(
                content=tags_ref,
                type=ValueSourceType.REF
            )
        )
        
        # 模拟循环过程 - 第一个循环项
        first_item = {
            "id": 1,
            "name": "Item 1",
            "details": {
                "description": "First item description",
                "tags": ["tag1", "tag2"]
            }
        }
        
        # 在上下文中设置当前循环项
        self.context.set_variable("current-item", "", first_item)
        
        # 解析引用
        resolved_tag = self.context.resolve_port_value(tags_port_value)
        
        # 验证结果
        self.assertEqual(resolved_tag, "tag2")
        
        # 模拟循环过程 - 第二个循环项
        second_item = {
            "id": 2,
            "name": "Item 2",
            "details": {
                "description": "Second item description",
                "tags": ["tag2", "tag3"]
            }
        }
        
        # 更新上下文中的当前循环项
        self.context.set_variable("current-item", "", second_item)
        
        # 解析引用
        resolved_tag = self.context.resolve_port_value(tags_port_value)
        
        # 验证结果
        self.assertEqual(resolved_tag, "tag3")
        
        # 退出循环模块的作用域
        self.context.exit_scope()
    
    def test_reference_from_loop_result(self):
        """测试引用循环结果中的嵌套属性"""
        # 模拟循环执行结果
        loop_results = [
            {"id": 1, "status": "success", "data": {"value": 100, "metadata": {"source": "API"}}},
            {"id": 2, "status": "success", "data": {"value": 200, "metadata": {"source": "DB"}}},
            {"id": 3, "status": "failed", "data": None}
        ]
        
        # 设置循环模块的输出
        self.context.set_variable(self.loop_module.module_id, "results", loop_results)
        
        # 创建引用循环结果中特定项目的引用
        result_ref = ReferenceValue(
            moduleID=self.loop_module.module_id,
            name="results",
            path="[1].data.value"  # 访问第二个结果的值
        )
        
        # 创建端口值
        port_value = PortValue(
            type=ValueType.INTEGER,
            value=ValueContent(
                content=result_ref,
                type=ValueSourceType.REF
            )
        )
        
        # 解析引用
        resolved_value = self.context.resolve_port_value(port_value)
        
        # 验证结果
        self.assertEqual(resolved_value, 200)
    
    def test_complex_loop_reference(self):
        """测试复杂的循环引用场景"""
        # 设置循环模块的上下文
        self.loop_module.set_context(self.context)
        
        # 进入循环模块的作用域
        self.context.enter_scope(self.loop_module.module_id)
        
        # 模拟更复杂的循环项目
        complex_item = {
            "id": "complex1",
            "nested": {
                "array": [
                    {"key": "a", "values": [1, 2, 3]},
                    {"key": "b", "values": [4, 5, 6]}
                ],
                "map": {
                    "x": {"label": "X", "data": [{"type": "point", "coords": [10, 20]}]},
                    "y": {"label": "Y", "data": [{"type": "line", "coords": [30, 40]}]}
                }
            }
        }
        
        # 设置当前循环项
        self.context.set_variable("current-item", "", complex_item)
        
        # 创建深度嵌套的引用
        deep_ref = ReferenceValue(
            moduleID="current-item",
            name="",
            path="nested.array[1].values[2]"  # 访问deeply嵌套的值
        )
        
        # 创建对嵌套映射的引用
        map_ref = ReferenceValue(
            moduleID="current-item",
            name="",
            path="nested.map.x.data[0].coords[1]"  # 访问嵌套映射中的值
        )
        
        # 创建端口值
        array_port_value = PortValue(
            type=ValueType.INTEGER,
            value=ValueContent(
                content=deep_ref,
                type=ValueSourceType.REF
            )
        )
        
        map_port_value = PortValue(
            type=ValueType.INTEGER,
            value=ValueContent(
                content=map_ref,
                type=ValueSourceType.REF
            )
        )
        
        # 解析引用
        array_value = self.context.resolve_port_value(array_port_value)
        map_value = self.context.resolve_port_value(map_port_value)
        
        # 验证结果
        self.assertEqual(array_value, 6)  # nested.array[1].values[2]
        self.assertEqual(map_value, 20)   # nested.map.x.data[0].coords[1]
        
        # 退出循环模块的作用域
        self.context.exit_scope()


if __name__ == "__main__":
    unittest.main() 