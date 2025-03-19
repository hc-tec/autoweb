from abc import ABC, abstractmethod
from typing import List, Dict, Any
import openpyxl

from taskflow.task_blocks.extract_data_block import Field


class DataExporter(ABC):

    @abstractmethod
    def export(self, fields_order: List[str], fields: Dict[str, Any]) -> None:
        ...


def get_value(value_list: List[Any],
              index: int) -> Any:
    if index >= len(value_list):
        return value_list[-1]
    return value_list[index]


def construct_data_row(fields_order: List[str], fields: Dict[str, Any], index: int) -> List[Any]:
    data_row = []
    for field_name in fields_order:
        field = fields[field_name]
        data_row.append(get_value(field, index))
    return data_row


class ExcelExporter(DataExporter):

    def __init__(self, name: str):
        self.name = name
        self.workbook = openpyxl.Workbook()
        self.sheet = self.workbook.active

    def export(self, fields_order: List[str], fields: Dict[str, Any]) -> None:
        values = fields.values()
        if len(values) == 0:
            return
        size = max([len(value) for value in values])
        self.sheet.append(fields_order)

        for i in range(size):
            data_row = construct_data_row(fields_order, fields, i)
            self.sheet.append(data_row)

        self.workbook.save(self.name)
