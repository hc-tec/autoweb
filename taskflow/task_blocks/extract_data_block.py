import logging
from abc import abstractmethod, ABC
from typing import Optional, List, Any, Dict

from taskflow.block_context import BlockContext

from taskflow.task_blocks.block import Block, BlockExecuteParams, register_block


class FieldExtractor(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def extract(self, xpath: str, context: BlockContext) -> Any:
        ...


Extractor_MAP = {}


def register_extractor(extractor_type: str, extractor_class: FieldExtractor):
    Extractor_MAP[extractor_type] = extractor_class


class TextFieldExtractor(FieldExtractor):
    def extract(self, xpath: str, context: BlockContext) -> Any:
        return context.browser.get_element_text(xpath)


register_extractor("TextFieldExtractor", TextFieldExtractor)


class Field:

    def __init__(self, name: str, xpath: str):
        self.name = name
        self.xpath = xpath
        self.type = None
        self.value = None
        self.default_value = None
        self.extractor: Optional[FieldExtractor] = None
        self.need_export = True

    def set_extractor(self, extractor: FieldExtractor):
        self.extractor = extractor
        return self

    def extract(self, absolute_path: str, context: BlockContext) -> Any:
        self.value = self.extractor.extract("{}{}".format(absolute_path,
                                                          self.xpath),
                                            context)
        logging.debug(self)
        return self.value

    def get_value(self) -> Optional[Any]:
        return self.value or self.default_value

    def load_from_config(self, config: Dict):
        self.name = config["name"]
        self.xpath = config["xpath"]
        self.type = config.get("type")
        self.default_value = config.get("default_value")
        self.need_export = config.get("need_export", True)
        extractor = config.get("field_extractor")
        self.extractor = Extractor_MAP[extractor](extractor)

    def __str__(self):
        return "Field(name={}, xpath={}, type={}, value={}, default_value={}, need_export=False)".format(
            self.name,
            self.xpath,
            self.type,
            self.value,
            self.default_value,
            self.need_export
        )

    __repr__ = __str__


class ExtractDataBlock(Block):

    class Delegate(ABC):
        @abstractmethod
        def on_field_extracted(self, field: Field):
            ...

    def __init__(self, name: str, context: BlockContext, **kwargs):
        super().__init__(name, context)
        self.field_list: List[Field] = []
        self.field_observer: Optional[ExtractDataBlock.Delegate] = None

    def set_field_observer(self, field_observer: 'ExtractDataBlock.Delegate'):
        self.field_observer = field_observer

    def execute(self, params: BlockExecuteParams):
        loop_item_xpath = ""
        if self.use_relative_xpath:
            loop_item_xpath = params.get_loop_item(self.depth - 1)
            
        # 提取所有字段
        results = []
        for field in self.field_list:
            value = field.extract(loop_item_xpath, self.context)
            self.on_field_extract(field)
            results.append({
                "name": field.name,
                "value": value
            })
            
        # 如果需要输出到变量系统
        if "results" in self.output_variables:
            params.set_variable("results", results)
            
        if "result_count" in self.output_variables:
            params.set_variable("result_count", len(results))
            
        return results

    def on_field_extract(self, field: Field):
        if self.field_observer:
            self.field_observer.on_field_extracted(field)

    def add_field_list(self, field_list: List[Field]):
        self.field_list.extend(field_list)

    def add_field(self, field: Field):
        self.field_list.append(field)

    def remove_field(self, field: Field):
        self.field_list.remove(field)

    def load_from_config(self, control_flow, config: Dict):
        use_relative_xpath = config.get("use_relative_xpath", False)
        if isinstance(use_relative_xpath, str):
            self.use_relative_xpath = use_relative_xpath.lower() == "true"
        else:
            self.use_relative_xpath = bool(use_relative_xpath)
            
        self.set_field_observer(control_flow.get_field_saver())
        
        # 从配置中加载字段
        for field_config in config.get("fields", []):
            field = Field(field_config["name"], field_config["xpath"])
            
            # 设置提取器
            extractor_type = field_config.get("extractor_type", "TextFieldExtractor")
            if extractor_type in Extractor_MAP:
                extractor = Extractor_MAP[extractor_type](extractor_type)
                field.set_extractor(extractor)
            else:
                # 默认使用文本提取器
                field.set_extractor(TextFieldExtractor("默认文本提取器"))
                
            self.add_field(field)


register_block("ExtractDataBlock", ExtractDataBlock)
