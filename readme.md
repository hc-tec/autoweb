# AutoWeb 自动化工作流系统

AutoWeb是一个强大的自动化工作流系统，用于构建和执行复杂的Web自动化任务。该系统提供了灵活的模块化架构，支持多种类型的模块和数据处理能力。

**目前功能非常不完善，欢迎感兴趣的开发者一起参与开发，欢迎star，共同完善这个项目，为网页自动化贡献一份力量**

本仓库包含自动化代码（Taskflow）和工作流执行引擎代码（Workflow）
前端代码位于https://github.com/hc-tec/autoweb-frontend

## 功能特性

### 1. 模块化架构
- **基础模块类型**
  - 原子模块 (AtomicModule)
  - 组合模块 (CompositeModule)
  - 插槽模块 (SlotModule)
  - 事件触发模块 (EventTriggerModule)
  - Python代码模块 (PythonCodeModule)
  - 循环模块 (LoopModule)
  - 自定义模块 (CustomModule)
  - 输入模块 (InputModule)
  - 输出模块 (OutputModule)

### 2. 数据处理能力
- 支持多种数据类型的输入输出
- 灵活的数据格式化和转换
- 复杂的数据引用和变量解析
- 上下文管理和数据传递

### 3. 工作流控制
- 条件判断和分支控制
- 循环和迭代处理
- 事件触发机制
- 错误处理和恢复

### 4. 扩展性
- 自定义模块支持
- 插件化架构
- 灵活的配置系统

## 安装说明

1. 克隆项目
```bash
git clone [项目地址]
cd autoweb
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

## 使用示例

### 1. 创建简单工作流

```python
from workflow import Module, ModuleType, ModuleMeta
from workflow.modules import InputModule, OutputModule, PythonCodeModule

# 创建输入模块
input_module = InputModule("workflow_input")
input_module.add_input_variable("name", ValueType.STRING, "用户姓名", required=True)

# 创建处理模块
process_module = PythonCodeModule("process")
process_module.set_code("""
def process(inputs):
    return {"greeting": f"Hello, {inputs['name']}!"}
""")

# 创建输出模块
output_module = OutputModule("workflow_output")
output_module.add_output_variable("greeting", ValueType.STRING, "问候语")

# 设置模块连接
process_module.set_input("name", input_module.get_output("name"))
output_module.set_input("greeting", process_module.get_output("greeting"))
```

### 2. 使用循环模块

```python
from workflow.modules import LoopModule

# 创建循环模块
loop_module = LoopModule("loop")
loop_module.set_loop_body(process_module)
loop_module.set_input("items", input_module.get_output("items"))
```

## 项目结构

```
autoweb/
├── workflow/           # 工作流核心模块
│   ├── modules/       # 模块定义
│   ├── module_port.py # 端口定义
│   └── module_context.py # 上下文管理
├── autoweb/           # 自动化Web模块
├── browser/           # 浏览器控制模块
├── taskflow/          # 任务流管理
└── requirements.txt   # 项目依赖
```

## 开发指南

### 1. 创建新模块
1. 在 `workflow/modules/` 目录下创建新的模块文件
2. 继承基础模块类（如 `AtomicModule` 或 `CompositeModule`）
3. 实现必要的接口和方法
4. 在 `__init__.py` 中注册新模块

### 2. 添加新功能
1. 遵循模块化设计原则
2. 确保向后兼容性
3. 添加适当的文档和测试

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 联系方式

2598772546@qq.com