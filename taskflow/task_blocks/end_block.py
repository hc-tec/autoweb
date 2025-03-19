import logging
from abc import ABC, abstractmethod
from typing import Callable, Dict

from taskflow.block_context import BlockContext
from taskflow.task_blocks.block import Block, BlockExecuteParams, register_block


class EndBlock(Block):
    class Observer:
        def __init__(self):
            self.observers = []

        def append_observer(self, observer: Callable):
            logging.debug("append observer: {}".format(observer))
            self.observers.append(observer)

        def remove_observer(self, observer: Callable):
            logging.debug("remove observer: {}".format(observer))
            self.observers.remove(observer)

        def on_end(self):
            logging.info("on end: Call observer")
            for observer in self.observers:
                observer()

    def __init__(self, name: str, context: BlockContext, **kwargs):
        super().__init__(name, context)
        self.observer = EndBlock.Observer()

    def observe(self, observer: Callable):
        self.observer.append_observer(observer)

    def execute(self, params: BlockExecuteParams):
        logging.info("EndBlock[{}] execute".format(self.name))
        self.observer.on_end()

    def load_from_config(self, control_flow, config: Dict):
        pass


register_block("EndBlock", EndBlock)


