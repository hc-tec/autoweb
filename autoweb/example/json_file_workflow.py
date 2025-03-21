import sys
import os
import asyncio
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from workflow.module_parser import ModuleParser
from workflow.module_context import ModuleContext
from workflow.module_visualizer import ModuleVisualizer

# 确保适配器模块已注册
from autoweb.modules_adapter import register_adapters_to_parser
import logging
logging.basicConfig(level=logging.INFO)


async def run_example(json_file_path: str):
    """
    运行JSON文件配置的工作流示例
    
    Args:
        json_file_path: JSON配置文件路径
    """
    print(f"从文件 {json_file_path} 加载JSON工作流配置...")
    
    # 解析JSON配置文件
    workflow = ModuleParser.load_from_file(json_file_path)
    
    # 可视化工作流
    print("\n工作流结构:")
    ModuleVisualizer.print_tree(workflow)
    
    # 创建上下文
    context = ModuleContext()
    workflow.set_context(context)
    
    # 执行工作流
    print("\n开始执行工作流...")
    result = await workflow.execute()
    
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
    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # JSON配置文件路径
    json_file_path = os.path.join(current_dir, "json_workflow.json")
    
    # 运行示例
    asyncio.run(run_example(json_file_path)) 