import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from typing import Dict, Any
from workflow.module_visualizer import ModuleVisualizer

from workflow.module import (
    Module, AtomicModule, CompositeModule, SlotModule, 
    EventTriggerModule, ModuleMeta, ModuleType
)
from workflow.module_port import (
    ModuleInputs, ModuleOutputs, InputDefinition, OutputDefinition,
    InputParameter, ValueType, InputHelper
)
from workflow.module_context import ModuleContext, ModuleExecutionResult


class SimpleModule(AtomicModule):
    """简单测试模块"""
    
    def __init__(self, module_id: str, value: str = "默认值"):
        super().__init__(module_id)
        self.value = value
        
        # 设置元数据
        meta = ModuleMeta(
            title="简单模块",
            description="简单的测试模块",
            category="test"
        )
        self.set_meta(meta)
        
        # 设置输入和输出
        input_defs = [
            InputDefinition(
                name="input_value",
                type=ValueType.STRING,
                description="输入值",
                required=False
            )
        ]
        
        output_defs = [
            OutputDefinition(
                name="output_value",
                type=ValueType.STRING,
                description="输出值"
            )
        ]
        
        self.set_inputs(ModuleInputs(
            inputDefs=input_defs,
            inputParameters=[
                InputParameter(
                    name="input_value",
                    input=InputHelper.create_literal_value(ValueType.STRING, value)
                )
            ]
        ))
        
        self.set_outputs(ModuleOutputs(outputDefs=output_defs))
    
    def execute(self) -> ModuleExecutionResult:
        """执行模块逻辑"""
        if not self.context:
            return ModuleExecutionResult(
                success=False,
                outputs={},
                error="Context not set"
            )
            
        # 进入模块作用域
        self.context.enter_scope(self.module_id)
        
        try:
            # 解析输入参数
            input_value = self.context.resolve_port_value(
                self.inputs.inputParameters[0].input
            )
            
            # 存储输入到上下文
            self.context.set_variable(self.module_id, "input_value", input_value)
            
            # 生成输出
            output_value = f"处理结果: {input_value}"
            
            # 存储输出到上下文
            self.context.set_variable(self.module_id, "output_value", output_value)
            
            return ModuleExecutionResult(
                success=True,
                outputs={"output_value": output_value}
            )
        finally:
            # 确保离开模块作用域
            self.context.exit_scope()


class DataProviderModule(AtomicModule):
    """数据提供模块"""
    
    def __init__(self, module_id: str, data: str = "测试数据"):
        super().__init__(module_id)
        self.data = data
        
        # 设置元数据
        meta = ModuleMeta(
            title="数据提供者",
            description="提供数据",
            category="data"
        )
        self.set_meta(meta)
        
        # 设置输出
        output_defs = [
            OutputDefinition(
                name="data",
                type=ValueType.STRING,
                description="提供的数据"
            )
        ]
        
        self.set_inputs(ModuleInputs(inputDefs=[], inputParameters=[]))
        self.set_outputs(ModuleOutputs(outputDefs=output_defs))
    
    def _execute_internal(self) -> ModuleExecutionResult:
        """执行模块逻辑"""
        # 存储数据到上下文
        self.context.set_variable(self.module_id, "data", self.data)
        return ModuleExecutionResult(
            success=True,
            outputs={"data": self.data}
        )


class DataProcessorModule(AtomicModule):
    """数据处理模块"""
    
    def __init__(self, module_id: str):
        super().__init__(module_id)
        
        # 设置元数据
        meta = ModuleMeta(
            title="数据处理器",
            description="处理接收到的数据",
            category="data"
        )
        self.set_meta(meta)
        
        # 设置输入和输出
        input_defs = [
            InputDefinition(
                name="data",
                type=ValueType.STRING,
                description="要处理的数据",
                required=True
            )
        ]
        
        output_defs = [
            OutputDefinition(
                name="processed_data",
                type=ValueType.STRING,
                description="处理后的数据"
            )
        ]
        
        self.set_inputs(ModuleInputs(
            inputDefs=input_defs,
            inputParameters=[]  # 将在测试中设置
        ))
        
        self.set_outputs(ModuleOutputs(outputDefs=output_defs))

    def _execute_internal(self) -> ModuleExecutionResult:
        """执行模块逻辑"""
        # 获取输入数据
        data = self.context.get_variable(self.module_id, "data")
        
        # 处理数据
        processed_data = f"处理后的数据: {data.upper()}"
        
        return ModuleExecutionResult(
            success=True,
            outputs={"processed_data": processed_data}
        )


class ErrorHandlerModule(AtomicModule):
    """错误处理模块"""
    
    def __init__(self, module_id: str):
        super().__init__(module_id)
        
        meta = ModuleMeta(
            title="错误处理器",
            description="处理流水线中的错误",
            category="error"
        )
        self.set_meta(meta)
        
        input_defs = [
            InputDefinition(
                name="error_message",
                type=ValueType.STRING,
                description="错误信息",
                required=True
            )
        ]
        
        output_defs = [
            OutputDefinition(
                name="handled_error",
                type=ValueType.STRING,
                description="处理后的错误信息"
            )
        ]
        
        self.set_inputs(ModuleInputs(inputDefs=input_defs, inputParameters=[]))
        self.set_outputs(ModuleOutputs(outputDefs=output_defs))
        
    def _execute_internal(self) -> ModuleExecutionResult:
        error_message = self.context.get_variable(self.module_id, "error_message")
        handled_message = f"已处理错误: {error_message}"
        
        return ModuleExecutionResult(
            success=True,
            outputs={"handled_error": handled_message}
        )


class DataValidatorModule(AtomicModule):
    """数据验证模块"""
    
    def __init__(self, module_id: str):
        super().__init__(module_id)
        
        meta = ModuleMeta(
            title="数据验证器",
            description="验证数据格式和内容",
            category="validation"
        )
        self.set_meta(meta)
        
        input_defs = [
            InputDefinition(
                name="data",
                type=ValueType.STRING,
                description="要验证的数据",
                required=True
            )
        ]
        
        output_defs = [
            OutputDefinition(
                name="validation_result",
                type=ValueType.STRING,
                description="验证结果"
            ),
            OutputDefinition(
                name="is_valid",
                type=ValueType.BOOLEAN,
                description="是否有效"
            )
        ]
        
        self.set_inputs(ModuleInputs(inputDefs=input_defs, inputParameters=[]))
        self.set_outputs(ModuleOutputs(outputDefs=output_defs))
        
    def _execute_internal(self) -> ModuleExecutionResult:
        data = self.context.get_variable(self.module_id, "data")
        
        # 简单的验证逻辑：检查数据是否包含特定关键词
        is_valid = "error" not in data.lower()
        validation_result = "数据有效" if is_valid else "数据无效"
        
        if not is_valid:
            # 触发错误事件
            self.trigger_event("validation_error", {"error_message": "数据验证失败"})
            
        return ModuleExecutionResult(
            success=True,
            outputs={
                "validation_result": validation_result,
                "is_valid": is_valid
            }
        )


class TestCompositeEvents(unittest.TestCase):
    """测试组合模块和事件系统"""
    
    # def test_simple_composite_execution(self):
    #     """测试简单的组合模块执行"""
    #     # 创建组合模块
    #     composite = CompositeModule("composite")
        
    #     # 添加两个简单模块
    #     module1 = SimpleModule("module1", "值1")
    #     module2 = SimpleModule("module2", "值2")
        
    #     # 添加到组合模块
    #     composite.add_module(module1)
    #     composite.add_module(module2)
        
    #     # 创建上下文
    #     context = ModuleContext()
    #     composite.set_context(context)
        
    #     # 执行组合模块
    #     result = composite.execute()
        
    #     # 验证结果
    #     self.assertTrue(result.success)
    #     self.assertIn("modules", result.child_results)
    #     self.assertEqual(len(result.child_results["modules"]), 2)
        
    #     # 验证子模块结果
    #     module1_result = result.child_results["modules"][0]
    #     self.assertTrue(module1_result.success)
    #     self.assertEqual(module1_result.outputs["output_value"], "处理结果: 值1")
        
    #     module2_result = result.child_results["modules"][1]
    #     self.assertTrue(module2_result.success)
    #     self.assertEqual(module2_result.outputs["output_value"], "处理结果: 值2")
    
    # def test_data_flow(self):
    #     """测试数据流"""
    #     # 创建组合模块
    #     composite = CompositeModule("composite")
        
    #     # 创建数据提供模块
    #     data_provider = DataProviderModule("data_provider", "原始数据")
        
    #     # 创建数据处理模块
    #     data_processor = DataProcessorModule("data_processor")
        
    #     # 设置数据处理模块的输入来自数据提供模块
    #     data_processor.set_inputs(ModuleInputs(
    #         inputDefs=data_processor.inputs.inputDefs,
    #         inputParameters=[
    #             InputParameter(
    #                 name="data",
    #                 input=InputHelper.create_reference_value(
    #                     ValueType.STRING,
    #                     "data_provider",
    #                     "data"
    #                 )
    #             )
    #         ]
    #     ))
        
    #     # 添加模块到组合模块
    #     composite.add_module(data_provider)
    #     composite.add_module(data_processor)
        
    #     # 创建上下文
    #     context = ModuleContext()
    #     composite.set_context(context)

    #     ModuleVisualizer.print_tree(composite)
        
    #     # 执行组合模块
    #     result = composite.execute()
        
    #     # 验证结果
    #     self.assertTrue(result.success)
        
    #     # 验证模块结果
    #     modules_results = result.child_results["modules"]
    #     self.assertEqual(len(modules_results), 2)
        
    #     # 验证数据提供模块结果
    #     data_provider_result = modules_results[0]
    #     self.assertTrue(data_provider_result.success)
    #     self.assertEqual(data_provider_result.outputs["data"], "原始数据")
        
    #     # 验证数据处理模块结果
    #     data_processor_result = modules_results[1]
    #     self.assertTrue(data_processor_result.success)
    #     self.assertEqual(data_processor_result.outputs["processed_data"], "处理后的数据: 原始数据".upper())
    
    # def test_explicit_event_trigger(self):
    #     """测试显式事件触发模块"""
    #     # 创建组合模块
    #     composite = CompositeModule("composite")
        
    #     # 创建简单模块
    #     simple_module = SimpleModule("simple_module", "普通值")
        
    #     # 创建事件触发模块
    #     trigger_module = EventTriggerModule(
    #         "trigger_module", 
    #         "customEvent", 
    #         {"message": "触发的自定义事件"}
    #     )
        
    #     # 添加模块到组合模块
    #     composite.add_module(simple_module)
    #     composite.add_module(trigger_module)
        
    #     # 创建上下文
    #     context = ModuleContext()
    #     composite.set_context(context)

    #     ModuleVisualizer.print_tree(composite)

    #     # 执行组合模块
    #     result = composite.execute()
        
    #     # 验证结果
    #     self.assertTrue(result.success)
        
    #     # 验证模块结果
    #     modules_results = result.child_results["modules"]
    #     self.assertEqual(len(modules_results), 2)
        
    #     # 验证简单模块结果
    #     simple_result = modules_results[0]
    #     self.assertTrue(simple_result.success)
        
    #     # 验证事件触发模块结果
    #     trigger_result = modules_results[1]
    #     self.assertTrue(trigger_result.success)

    def test_complex_data_pipeline(self):
        """测试复杂的数据处理流水线"""
        # 创建主流水线
        pipeline = CompositeModule("main_pipeline")
        pipeline.set_meta(ModuleMeta(
            title="主数据处理流水线",
            description="包含数据采集、处理和验证的完整流水线",
            category="pipeline"
        ))
        
        # 创建数据采集阶段
        data_collection = CompositeModule("data_collection")
        data_collection.set_meta(ModuleMeta(
            title="数据采集阶段",
            description="负责数据的采集和初步处理",
            category="stage"
        ))
        data_collection.set_outputs(ModuleOutputs(outputDefs=[
            OutputDefinition(
                name="processed_data",
                type=ValueType.STRING,
                description="采集到的数据"
            )
        ]))
        
        # 添加数据提供者
        provider = DataProviderModule("data_provider", "测试数据 #123")
        data_collection.add_module(provider)
        
        # 添加初步处理
        processor = DataProcessorModule("initial_processor")
        processor.set_inputs(ModuleInputs(
            inputDefs=processor.inputs.inputDefs,
            inputParameters=[
                InputParameter(
                    name="data",
                    input=InputHelper.create_reference_value(
                        ValueType.STRING,
                        "data_provider",
                        "data"
                    )
                )
            ]
        ))
        processor.set_outputs(ModuleOutputs(outputDefs=[
            OutputDefinition(
                name="processed_data",
                type=ValueType.STRING,
                description="处理后的数据"
            )
        ]))
        data_collection.add_module(processor)
        
        # 创建数据验证阶段
        validation_stage = CompositeModule("validation_stage")
        validation_stage.set_meta(ModuleMeta(
            title="数据验证阶段",
            description="验证数据的有效性",
            category="stage"
        ))
        validation_stage_inputdefs = [
            InputDefinition(
                name="data",
                type=ValueType.STRING,
                description="要验证的数据",
                required=True
            )
        ]
        validation_stage.set_inputs(
            ModuleInputs(inputDefs=validation_stage_inputdefs, inputParameters=[
            InputParameter(
                name="data",
                input=InputHelper.create_reference_value(
                    ValueType.STRING,
                    "data_collection",
                    "processed_data"
                )
            )
        ]))
        validation_stage.set_outputs(ModuleOutputs(outputDefs=[
            OutputDefinition(
                name="validation_result",
                type=ValueType.STRING,
                description="验证结果"
            )
        ]))
        

        # 添加验证器
        validator = DataValidatorModule("data_validator")
        validator.set_inputs(ModuleInputs(
            inputDefs=validator.inputs.inputDefs,
            inputParameters=[
                InputParameter(
                    name="data",
                    input=InputHelper.create_reference_value(
                        ValueType.STRING,
                        "validation_stage",
                        "data"
                    )
                )
            ]
        ))
        validation_stage.set_outputs(ModuleOutputs(outputDefs=[
            OutputDefinition(
                name="validation_result",
                type=ValueType.STRING,
                description="验证结果"
            ),
            OutputDefinition(
                name="is_valid",
                type=ValueType.BOOLEAN,
                description="是否有效"
            )   
        ]))
        validation_stage.add_module(validator)
        
        # 添加错误处理插槽
        error_slot = validation_stage.add_slot("error_handler", "处理验证错误")
        
        # 添加错误处理器到插槽
        error_handler = ErrorHandlerModule("validation_error_handler")
        error_handler.set_inputs(ModuleInputs(
            inputDefs=error_handler.inputs.inputDefs,
            inputParameters=[
                InputParameter(
                    name="error_message",
                    input=InputHelper.create_literal_value(
                        ValueType.STRING,
                        "验证过程中发生错误"
                    )
                )
            ]
        ))
        error_slot.add_module(error_handler)
        
        # 添加事件触发器，连接验证错误和错误处理插槽
        error_trigger = EventTriggerModule(
            "error_trigger",
            "validation_error",
            {"message": "发生验证错误"}
        )
        validation_stage.add_module(error_trigger)
        
        # 将各个阶段添加到主流水线
        pipeline.add_module(data_collection)
        pipeline.add_module(validation_stage)
        
        # 创建上下文并执行
        context = ModuleContext()
        pipeline.set_context(context)
        
        # 可视化流水线结构
        ModuleVisualizer.print_tree(pipeline)
        
        # 执行流水线
        result = pipeline.execute()
        
        # 验证结果
        self.assertTrue(result.success)
        self.assertIn("modules", result.child_results)
        
        # 验证数据采集阶段
        collection_result = result.child_results["modules"][0]
        self.assertTrue(collection_result.success)
        
        # 验证验证阶段
        validation_result = result.child_results["modules"][1]
        self.assertTrue(validation_result.success)
        
        # 打印执行结果
        print("\n执行结果:")
        print("─" * 50)
        print(f"数据采集阶段: {'成功' if collection_result.success else '失败'}")
        print(f"数据验证阶段: {'成功' if validation_result.success else '失败'}")
        print("─" * 50)


if __name__ == "__main__":
    unittest.main() 