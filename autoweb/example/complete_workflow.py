import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from workflow.module import CompositeModule, ModuleMeta
from workflow.module_port import ModuleInputs, ModuleOutputs, InputHelper, InputParameter, ValueType
from workflow.module_context import ModuleContext
from workflow.module_visualizer import ModuleVisualizer

from autoweb.modules_adapter import AdapterFactory


async def run_example():
    """
    运行一个完整的示例工作流，演示如何使用多个适配器
    """
    print("创建完整示例工作流...")
    
    # 创建主工作流模块
    main_workflow = CompositeModule("main_workflow")
    main_workflow.set_meta(ModuleMeta(
        title="完整示例工作流",
        description="使用多个 TaskFlow Block 适配器的完整示例工作流",
        category="example"
    ))
    
    # 设置空的输入输出
    main_workflow.set_inputs(ModuleInputs(inputDefs=[], inputParameters=[]))
    main_workflow.set_outputs(ModuleOutputs(outputDefs=[]))
    
    # 2. 创建打开页面模块适配器
    open_page_adapter = AdapterFactory.create_adapter("OpenPageBlock", "open_page_module", "打开菜鸟教程")
    
    # 设置URL参数
    url_value = InputHelper.create_literal_value(ValueType.STRING, "https://www.runoob.com/")
    open_page_adapter.inputs.inputParameters.append(
        InputParameter(name="page_url", input=url_value)
    )
    
    # 添加到主工作流
    main_workflow.add_module(open_page_adapter)
    
    # 3. 创建输入框模块适配器
    input_adapter = AdapterFactory.create_adapter("InputBlock", "input_module", "输入搜索关键词")
    
    # 设置输入参数
    xpath_value = InputHelper.create_literal_value(ValueType.STRING, "/html/body/div[1]/div/div[1]/div/div[1]/div/form/input")
    text_value = InputHelper.create_literal_value(ValueType.STRING, "Python 教程")
    clear_first_value = InputHelper.create_literal_value(ValueType.BOOLEAN, True)
    
    input_adapter.inputs.inputParameters.extend([
        InputParameter(name="xpath", input=xpath_value),
        InputParameter(name="text", input=text_value),
        InputParameter(name="clear_first", input=clear_first_value)
    ])
    
    # 添加到主工作流
    main_workflow.add_module(input_adapter)
    
    # 4. 创建点击元素模块适配器
    click_adapter = AdapterFactory.create_adapter("ClickElementBlock", "click_module", "点击搜索按钮")
    
    # 设置参数
    search_button_xpath = InputHelper.create_literal_value(
        ValueType.STRING, 
        "/html/body/div[1]/div/div[1]/div/div[1]/div/form/button"
    )
    
    click_adapter.inputs.inputParameters.append(
        InputParameter(name="xpath", input=search_button_xpath)
    )
    
    # 添加到主工作流
    main_workflow.add_module(click_adapter)
    
    # 5. 创建数据提取模块适配器
    extract_adapter = AdapterFactory.create_adapter("ExtractDataBlock", "extract_module", "提取搜索结果")
    
    # 设置字段参数
    fields_value = InputHelper.create_literal_value(ValueType.ARRAY, [
        {
            "name": "标题",
            "xpath": "/html/body/div[3]/div/div[2]/div/div/ul/li[1]/div/div/h2/a",
            "extractor_type": "TextFieldExtractor"
        },
        {
            "name": "摘要",
            "xpath": "/html/body/div[3]/div/div[2]/div/div/ul/li[1]/div/div/p",
            "extractor_type": "TextFieldExtractor"
        }
    ])
    
    extract_adapter.inputs.inputParameters.extend([
        InputParameter(name="fields", input=fields_value),
        InputParameter(name="export_to_excel", input=InputHelper.create_literal_value(ValueType.BOOLEAN, True))
    ])
    
    # 添加到主工作流
    main_workflow.add_module(extract_adapter)
    
    # 可视化工作流
    print("\n工作流结构:")
    ModuleVisualizer.print_tree(main_workflow)
    
    # 创建上下文
    context = ModuleContext()
    main_workflow.set_context(context)
    
    # 执行工作流
    print("\n开始执行工作流...")
    result = await main_workflow.execute()
    
    # 输出结果
    print("\n执行结果:")
    print("─" * 50)
    print(f"成功状态: {'成功' if result.success else '失败'}")
    
    if result.outputs:
        print("\n输出变量:")
        for key, value in result.outputs.items():
            print(f"  - {key}: {value}")
    
    if result.error:
        print(f"\n错误信息: {result.error}")
    
    print("\n子模块执行结果:")
    if result.child_results and "modules" in result.child_results:
        for i, child_result in enumerate(result.child_results["modules"]):
            print(f"  - 模块 {i+1}: {'成功' if child_result.success else '失败'}")
            
            if child_result.outputs:
                for key, value in child_result.outputs.items():
                    print(f"    {key}: {value}")
    
    print("─" * 50)
    
    # 等待用户输入后关闭浏览器
    input("按Enter键关闭浏览器并退出...")
    
    # 关闭浏览器实例
    from autoweb.modules_adapter.base_adapter import BlockModuleAdapter
    BlockModuleAdapter.close_browser()
    
    return result


if __name__ == "__main__":
    asyncio.run(run_example()) 