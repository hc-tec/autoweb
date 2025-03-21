import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import unittest
from workflow.module import PythonCodeModule
from workflow.module_port import (
    ModuleInputs, ModuleOutputs, InputDefinition,
    OutputDefinition, InputParameter, ValueType, InputHelper
)
from workflow.module_context import ModuleContext


class TestPythonCodeModule(unittest.IsolatedAsyncioTestCase):
    """测试Python代码模块"""
    
    async def asyncSetUp(self):
        # 创建同步代码模块
        self.sync_module = PythonCodeModule("sync_module")
        sync_code = '''
def main(args: Args) -> Output:
    params = args.params
    
    lines = params['input'].strip().split('\\n')
    
    # 初始化两个数组
    male_lines = []
    female_lines = []
    
    # 遍历每一行，根据前缀将对白添加到对应的数组中
    for line in lines:
        if line.startswith('男：'):
            male_lines.append(line[2:])
        elif line.startswith('女：'):
            female_lines.append(line[2:])
    
    return {
        "male_lines": male_lines,
        "female_lines": female_lines
    }
'''
        self.sync_module.set_code(sync_code)
        
        # 创建异步代码模块
        self.async_module = PythonCodeModule("async_module")
        async_code = '''
async def main(args: Args) -> Output:
    params = args.params
    
    lines = params['input'].strip().split('\\n')
    
    # 模拟异步处理
    await asyncio.sleep(0.1)
    
    # 初始化两个数组
    male_lines = []
    female_lines = []
    
    # 遍历每一行，根据前缀将对白添加到对应的数组中
    for line in lines:
        if line.startswith('男：'):
            male_lines.append(line[2:])
        elif line.startswith('女：'):
            female_lines.append(line[2:])
    
    return {
        "male_lines": male_lines,
        "female_lines": female_lines
    }
'''
        self.async_module.set_code(async_code)
        
        # 设置输入输出定义
        input_defs = [
            InputDefinition(
                name="input",
                type=ValueType.STRING,
                description="要分割的对话文本",
                required=True
            )
        ]
        
        output_defs = [
            OutputDefinition(
                name="male_lines",
                type=ValueType.ARRAY,
                description="男性对白列表"
            ),
            OutputDefinition(
                name="female_lines",
                type=ValueType.ARRAY,
                description="女性对白列表"
            )
        ]
        
        # 设置输入参数
        test_input = ModuleInputs(
            inputDefs=input_defs,
            inputParameters=[
                InputParameter(
                    name="input",
                    input=InputHelper.create_literal_value(
                        ValueType.STRING,
                        "男：你好\n女：你好\n男：今天天气真好\n女：是的"
                    )
                )
            ]
        )
        
        # 设置输出定义
        test_output = ModuleOutputs(outputDefs=output_defs)
        
        # 配置模块
        for module in [self.sync_module, self.async_module]:
            module.set_inputs(test_input)
            module.set_outputs(test_output)
            
    async def test_sync_code(self):
        """测试同步代码执行"""
        context = ModuleContext()
        self.sync_module.set_context(context)
        
        result = await self.sync_module.execute()
        
        self.assertTrue(result.success)
        self.assertIn("male_lines", result.outputs)
        self.assertIn("female_lines", result.outputs)
        
        male_lines = result.outputs["male_lines"]
        female_lines = result.outputs["female_lines"]
        
        self.assertEqual(male_lines, ["你好", "今天天气真好"])
        self.assertEqual(female_lines, ["你好", "是的"])
        
    async def test_async_code(self):
        """测试异步代码执行"""
        context = ModuleContext()
        self.async_module.set_context(context)
        
        result = await self.async_module.execute()
        
        self.assertTrue(result.success)
        self.assertIn("male_lines", result.outputs)
        self.assertIn("female_lines", result.outputs)
        
        male_lines = result.outputs["male_lines"]
        female_lines = result.outputs["female_lines"]
        
        self.assertEqual(male_lines, ["你好", "今天天气真好"])
        self.assertEqual(female_lines, ["你好", "是的"])
        
    async def test_invalid_code(self):
        """测试无效代码"""
        module = PythonCodeModule("invalid_module")
        
        # 测试没有main函数的代码
        module.set_code("print('Hello')")
        
        context = ModuleContext()
        module.set_context(context)
        
        result = await module.execute()
        self.assertFalse(result.success)
        self.assertEqual(result.error, "No main function defined in code")
        
        # 测试返回非字典的代码
        module.set_code('''
def main(args: Args) -> Output:
    return "Not a dict"
''')
        
        result = await module.execute()
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Main function must return a dictionary")


if __name__ == "__main__":
    unittest.main() 