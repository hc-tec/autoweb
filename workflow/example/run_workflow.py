import sys
import os
import asyncio
import json
from pathlib import Path

# 添加上级目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from workflow.module_parser import ModuleParser
from workflow.module_context import ModuleContext
from workflow.module_visualizer import ModuleVisualizer
from workflow.module_port import InputHelper, ModuleInputs, ValueType


async def run_workflow(workflow_file):
    """
    加载并执行工作流
    
    Args:
        workflow_file: 工作流JSON文件路径
        input_data: 可选的输入数据
    """
    print(f"加载工作流: {workflow_file}")
    
    # 读取工作流定义
    with open(workflow_file, 'r', encoding='utf-8') as f:
        workflow_json = json.load(f)
    
    # 解析为模块
    main_pipeline = ModuleParser.parse_module(workflow_json)
    
    # 设置上下文
    context = ModuleContext()
    main_pipeline.set_context(context)
    
    # 可视化流水线
    print("\n工作流结构:")
    ModuleVisualizer.print_tree(main_pipeline)
    
    # 执行流水线
    print("\n开始执行工作流...")
    result = await main_pipeline.execute()
    
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
            module_id = workflow_json["modules"][i]["module_id"]
            print(f"  - {module_id}: {'成功' if child_result.success else '失败'}")
    
    print("─" * 50)
    
    return result


async def main():
    # 确定工作流文件路径
    current_dir = Path(__file__).parent
    workflow_file = current_dir / "data_process_workflow.json"
    workflow_file_error = current_dir / "data_process_workflow_error.json"

    # 执行工作流
    await run_workflow(workflow_file)
    print("=" * 50)
    # await run_workflow(workflow_file_error)

if __name__ == "__main__":
    asyncio.run(main()) 