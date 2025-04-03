# 工作流引用系统

本模块实现了工作流系统中的变量引用机制，支持简单引用和复杂的嵌套引用结构。

## 引用系统特性

### 基本引用
- 支持通过模块ID和变量名引用其他模块的输出值
- 支持不同类型的值（字符串、整数、浮点数、布尔值、对象、数组）

### 增强的嵌套引用
- **路径访问**：支持通过点号路径（如`user.profile.email`）访问对象的嵌套属性
- **数组索引访问**：支持通过索引（如`items[0].name`）访问数组元素
- **属性直接访问**：支持通过property字段直接访问对象的顶层属性
- **组合访问**：支持同时使用property和path，例如先获取`roles`属性，再访问`[1]`索引

### 循环模块支持
- 支持在循环模块中引用当前循环项的属性
- 支持复杂嵌套数据结构的访问，如多层数组和对象

## 使用示例

### 基本引用
```json
{
  "moduleID": "data-source",
  "name": "user"
}
```

### 路径访问
```json
{
  "moduleID": "data-source",
  "name": "user",
  "path": "profile.email"
}
```

### 数组索引访问
```json
{
  "moduleID": "data-source",
  "name": "items",
  "path": "[0].name"
}
```

### 属性直接访问
```json
{
  "moduleID": "data-source",
  "name": "user",
  "property": "id"
}
```

### 组合访问
```json
{
  "moduleID": "data-source",
  "name": "user",
  "property": "roles",
  "path": "[1]"
}
```

### 循环项访问
```json
{
  "moduleID": "current-item",
  "name": "",
  "path": "details.description"
}
```

## 设计说明

引用系统的核心组件包括：

1. **ReferenceValue类**：表示引用，包含moduleID、name、path、property等字段
2. **ReferenceResolver类**：处理不同类型引用的解析策略
3. **ModuleContext类**：提供运行时变量解析功能
   - resolve_port_value：解析端口值
   - _resolve_reference_value：解析引用值
   - _resolve_nested_access：处理嵌套访问
   - _navigate_object_path：导航对象路径

## 扩展性

系统设计具有良好的扩展性：

- 可以轻松添加新的引用字段来支持更复杂的访问模式
- 可以实现新的解析策略来处理特殊类型的引用
- 遵循策略模式，使代码结构清晰且易于维护 