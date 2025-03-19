from typing import List, Dict, Any, Optional

from taskflow.data_exporter import DataExporter
from taskflow.task_blocks.extract_data_block import ExtractDataBlock, Field


class FieldSaver(ExtractDataBlock.Delegate):

    def __init__(self):
        self.fields_order: List[str] = []  # 控制字段的顺序
        self.fields: Dict[str, List[Any]] = {}  # 保存具体的数据
        self.fields_dict: Dict[str, Any] = {}  # 给 js 用的，获取循环项的值，field['name']
        self.data_exporter: Optional[DataExporter] = None

    def on_field_extracted(self, field: Field):
        if field.need_export:
            if field.name not in self.fields_order:
                self.fields_order.append(field.name)
            self.fields.setdefault(field.name, []).append(field.get_value())
        self.fields_dict[field.name] = field.value

    def set_data_exporter(self, data_exporter: DataExporter):
        self.data_exporter = data_exporter

    def save(self):
        self.data_exporter.export(self.fields_order, self.fields)
