from typing import List, Dict, Any
from .module import Module, CompositeModule, SlotModule
from .module_port import PortValue, ValueSourceType, ReferenceValue


class ModuleVisualizer:
    """模块结构可视化工具"""
    
    @staticmethod
    def _format_port_value(port_value: PortValue) -> str:
        """格式化端口值
        
        Args:
            port_value: 端口值对象
            
        Returns:
            格式化后的字符串
        """
        if port_value.value.type == ValueSourceType.LITERAL:
            return f"值: {port_value.value.content}"
        elif port_value.value.type == ValueSourceType.REF:
            ref = port_value.value.content
            if isinstance(ref, ReferenceValue):
                return f"引用: {ref.moduleID}.{ref.name}"
        return "未知类型"
    
    @staticmethod
    def _get_module_io_info(module: Module) -> Dict[str, Any]:
        """获取模块的输入输出信息
        
        Args:
            module: 要分析的模块
            
        Returns:
            包含输入输出信息的字典
        """
        info = {
            "inputs": [],
            "outputs": [],
            "dependencies": set()
        }
        
        # 收集输入信息
        if module.inputs and module.inputs.inputParameters:
            for param in module.inputs.inputParameters:
                param_info = f"{param.name}"
                if param.input:
                    param_info += f" ({ModuleVisualizer._format_port_value(param.input)})"
                    # 收集依赖关系
                    if param.input.value.type == ValueSourceType.REF:
                        ref = param.input.value.content
                        if isinstance(ref, ReferenceValue):
                            info["dependencies"].add(ref.moduleID)
                info["inputs"].append(param_info)
                
        # 收集输出信息
        if module.outputs and module.outputs.outputDefs:
            for output in module.outputs.outputDefs:
                info["outputs"].append(f"{output.name}: {output.type.value}")
                
        return info
    
    @staticmethod
    def generate_tree(module: Module, level: int = 0, prefix: str = "", is_last: bool = True) -> str:
        """生成模块树形结构图
        
        Args:
            module: 要可视化的模块
            level: 当前层级
            prefix: 前缀字符串
            is_last: 是否是当前层级的最后一个节点
            
        Returns:
            树形结构字符串
        """
        # 构建当前行
        result = []
        if level > 0:
            result.append(prefix)
            result.append("└── " if is_last else "├── ")
        
        # 添加模块基本信息
        module_type = module.module_type
        module_info = [
            module.module_id,
            f"({module_type})"
        ]
        
        # 如果有元数据，添加标题
        if module.meta:
            module_info.append(f"- {module.meta.title}")
            
        result.append(" ".join(module_info))
        result.append("\n")
        
        # 添加输入输出信息
        new_prefix = prefix + ("    " if is_last else "│   ")
        io_info = ModuleVisualizer._get_module_io_info(module)
        
        # 添加输入信息
        if io_info["inputs"]:
            result.append(new_prefix + "├── 输入:\n")
            for i, input_info in enumerate(io_info["inputs"]):
                is_last_input = (i == len(io_info["inputs"]) - 1)
                result.append(new_prefix + "│   " + ("└── " if is_last_input else "├── ") + input_info + "\n")
                
        # 添加输出信息
        if io_info["outputs"]:
            result.append(new_prefix + "├── 输出:\n")
            for i, output_info in enumerate(io_info["outputs"]):
                is_last_output = (i == len(io_info["outputs"]) - 1)
                result.append(new_prefix + "│   " + ("└── " if is_last_output else "├── ") + output_info + "\n")
                
        # 添加依赖信息
        if io_info["dependencies"]:
            result.append(new_prefix + "├── 依赖模块:\n")
            deps = sorted(io_info["dependencies"])
            for i, dep in enumerate(deps):
                is_last_dep = (i == len(deps) - 1)
                result.append(new_prefix + "│   " + ("└── " if is_last_dep else "├── ") + dep + "\n")
        
        # 处理子模块
        if isinstance(module, CompositeModule):
            new_prefix = prefix + ("    " if is_last else "│   ")
            
            # 获取所有子模块
            children = []
            children.extend(module.modules)  # 普通子模块
            
            # 如果是组合模块，添加插槽
            if hasattr(module, "slots"):
                for slot in module.slots.values():
                    children.append(slot)
            
            # 递归处理每个子模块
            for i, child in enumerate(children):
                is_last_child = (i == len(children) - 1)
                result.append(ModuleVisualizer.generate_tree(
                    child,
                    level + 1,
                    new_prefix,
                    is_last_child
                ))
        elif isinstance(module, SlotModule):
            # 处理插槽中的模块
            new_prefix = prefix + ("    " if is_last else "│   ")
            for i, slot_module in enumerate(module.modules):
                is_last_child = (i == len(module.modules) - 1)
                result.append(ModuleVisualizer.generate_tree(
                    slot_module,
                    level + 1,
                    new_prefix,
                    is_last_child
                ))
                
        return "".join(result)
    
    @staticmethod
    def print_tree(module: Module):
        """打印模块树形结构
        
        Args:
            module: 要可视化的模块
        """
        print("\n模块结构图:")
        print("─" * 80)
        print(ModuleVisualizer.generate_tree(module))
        print("─" * 80) 