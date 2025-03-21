from typing import Dict, Any, TypedDict, Optional
from dataclasses import dataclass

class Args:
    """模块执行参数"""
    def __init__(self, params: Dict[str, Any]):
        self.params = params
        
Output = Dict[str, Any]  # 模块输出类型

@dataclass
class CodeFunction:
    """Python代码函数定义"""
    code: str  # Python代码文本
    is_async: bool  # 是否是异步函数
    description: str = ""  # 函数描述
    
    @staticmethod
    def is_async_code(code: str) -> bool:
        """检查代码是否是异步函数
        
        Args:
            code: Python代码文本
            
        Returns:
            是否是异步函数
        """
        return code.strip().startswith("async")