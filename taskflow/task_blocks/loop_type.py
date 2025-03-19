from abc import abstractmethod, ABC
from typing import Tuple, Any, List


class LoopType(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def has_next(self) -> bool:
        ...

    @abstractmethod
    def get_next(self) -> Any:
        ...


LoopType_MAP = {}


def register_loop_type(loop_type_name: str, loop_type: LoopType):
    LoopType_MAP[loop_type_name] = loop_type


def get_loop_type(loop_type_name: str):
    return LoopType_MAP.get(loop_type_name, None)

class XPathLoopType(LoopType, ABC):
    ...


# 写一个固定元素的循环类型，接受xpath列表作为参数。
class FixedLoopType(XPathLoopType):

    def __init__(self, name: str, values: List[str], **kwargs):
        super().__init__(name)
        self.xpaths = values
        self.index = 0
        self.length = len(values)
        self.current_xpath = values[self.index]
        self.is_end = False
        self.current_element = None

    def has_next(self) -> bool:
        return self.index < self.length

    def get_next(self) -> Any:
        if self.index == self.length:
            return None
        self.current_xpath = self.xpaths[self.index]
        self.index += 1
        return self.current_xpath


register_loop_type("FixedLoopType", FixedLoopType)







