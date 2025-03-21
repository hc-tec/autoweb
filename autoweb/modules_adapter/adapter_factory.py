from typing import Dict, Type, Optional

from autoweb.modules_adapter.base_adapter import BlockModuleAdapter
from autoweb.modules_adapter.start_block_adapter import StartBlockAdapter
from autoweb.modules_adapter.open_page_block_adapter import OpenPageBlockAdapter
from autoweb.modules_adapter.click_element_block_adapter import ClickElementBlockAdapter
from autoweb.modules_adapter.extract_data_block_adapter import ExtractDataBlockAdapter
from autoweb.modules_adapter.input_block_adapter import InputBlockAdapter
# 将来其他适配器导入


class AdapterFactory:
    """适配器工厂，用于创建和管理各种Block适配器"""
    
    # 存储所有已注册的适配器类
    _adapter_classes: Dict[str, Type[BlockModuleAdapter]] = {}
    
    @classmethod
    def register_adapter(cls, block_name: str, adapter_class: Type[BlockModuleAdapter]):
        """注册适配器类"""
        cls._adapter_classes[block_name] = adapter_class
    
    @classmethod
    def create_adapter(cls, block_name: str, module_id: str, adapter_name: str = None) -> Optional[BlockModuleAdapter]:
        """
        创建适配器实例
        
        Args:
            block_name: 要适配的Block类名
            module_id: 模块ID
            adapter_name: 适配器名称(可选)
            
        Returns:
            BlockModuleAdapter: 适配器实例，如果未找到对应适配器则返回None
        """
        adapter_class = cls._adapter_classes.get(block_name)
        if not adapter_class:
            return None
            
        return adapter_class(module_id, adapter_name)
    
    @classmethod
    def initialize(cls):
        """初始化工厂，注册所有适配器"""
        # 注册所有的适配器
        cls.register_adapter("StartBlock", StartBlockAdapter)
        cls.register_adapter("OpenPageBlock", OpenPageBlockAdapter)
        cls.register_adapter("ClickElementBlock", ClickElementBlockAdapter)
        cls.register_adapter("ExtractDataBlock", ExtractDataBlockAdapter)
        cls.register_adapter("InputBlock", InputBlockAdapter)
        # 注册其他适配器...
        

# 初始化适配器工厂
AdapterFactory.initialize() 