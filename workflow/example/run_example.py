import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from workflow.module_context import ModuleContext
from workflow.module_parser import ModuleParser


pipeline = ModuleParser.load_from_file("workflow/example/data_process_workflow.json")


# 使用解析后的模块
context = ModuleContext()
pipeline.set_context(context)
result = pipeline.execute()

print(result)
