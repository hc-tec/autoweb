# 模块初始化文件
"""
TaskFlow Block 到 Workflow Module 的适配模块
"""

from autoweb.modules_adapter.base_adapter import BlockModuleAdapter
from autoweb.modules_adapter.start_block_adapter import StartBlockAdapter
from autoweb.modules_adapter.open_page_block_adapter import OpenPageBlockAdapter
from autoweb.modules_adapter.click_element_block_adapter import ClickElementBlockAdapter
from autoweb.modules_adapter.extract_data_block_adapter import ExtractDataBlockAdapter
from autoweb.modules_adapter.input_block_adapter import InputBlockAdapter
from autoweb.modules_adapter.adapter_factory import AdapterFactory

# 导出所有模块
__all__ = [
    'BlockModuleAdapter',
    'StartBlockAdapter',
    'OpenPageBlockAdapter',
    'ClickElementBlockAdapter',
    'ExtractDataBlockAdapter',
    'InputBlockAdapter',
    'AdapterFactory',
    'register_adapters_to_parser'
]


def register_adapters_to_parser():
    """
    将所有适配器模块注册到ModuleParser中
    """
    from workflow.module_parser import ModuleParser
    
    # 注册各种适配器模块
    ModuleParser.register_module_type("StartBlock", StartBlockAdapter)
    ModuleParser.register_module_type("OpenPageBlock", OpenPageBlockAdapter)
    ModuleParser.register_module_type("ClickElementBlock", ClickElementBlockAdapter)
    ModuleParser.register_module_type("ExtractDataBlock", ExtractDataBlockAdapter)
    ModuleParser.register_module_type("InputBlock", InputBlockAdapter)
    
    # 可以根据需要继续注册其他适配器模块
    
    print("已注册所有适配器模块到ModuleParser")


# 自动注册适配器到ModuleParser
register_adapters_to_parser() 