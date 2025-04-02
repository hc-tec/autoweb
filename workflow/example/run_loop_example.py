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

import logging
logging.basicConfig(level=logging.INFO)


async def run_loop_example(json_file_path: str):
    """
    运行循环示例
    
    Args:
        json_file_path: 循环示例JSON配置文件路径
    """
    print(f"从文件 {json_file_path} 加载循环示例配置...")
    
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
    
    print("─" * 50)
    
    return result


if __name__ == "__main__":
    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 循环示例JSON配置文件路径
    loop_example_file = os.path.join(current_dir, "loop_example.json")
    
    # 运行示例
    asyncio.run(run_loop_example(loop_example_file)) 