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

from autoweb.modules_adapter.adapter_factory import AdapterFactory
import logging
logging.basicConfig(level=logging.INFO)

async def run_example():
    """
    运行一个简单的示例工作流，演示如何使用适配器
    """
    print("创建示例工作流...")
    
    # 创建主工作流模块
    main_workflow = CompositeModule("main_workflow")
    main_workflow.set_meta(ModuleMeta(
        title="示例工作流",
        description="使用 TaskFlow Block 适配器的示例工作流",
        category="example"
    ))
    
    # 设置空的输入输出
    main_workflow.set_inputs(ModuleInputs(inputDefs=[], inputParameters=[]))
    main_workflow.set_outputs(ModuleOutputs(outputDefs=[]))
    
    # 创建开始模块适配器
    start_adapter = AdapterFactory.create_adapter("StartBlock", "start_module", "开始模块")
    main_workflow.add_module(start_adapter)
    
    # 创建打开页面模块适配器
    open_page_adapter = AdapterFactory.create_adapter("OpenPageBlock", "open_page_module", "打开菜鸟教程")
    
    # 设置URL参数
    url_value = InputHelper.create_literal_value(ValueType.STRING, "https://www.runoob.com/")
    open_page_adapter.inputs.inputParameters.append(
        InputParameter(name="page_url", input=url_value)
    )
    
    # 添加到主工作流
    main_workflow.add_module(open_page_adapter)
    
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