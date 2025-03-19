import logging

from taskflow.control_flow import ControlFlow
from taskflow.field_saver import FieldSaver
from taskflow.json_flow_parser import JsonFlowParser
from taskflow.task_blocks.block import BlockFactory
from taskflow.task_blocks.click_element_block import ClickElementBlock
from taskflow.task_blocks.condition_block import ExecJavaScriptConditionBlock, PassConditionBlock
from taskflow.data_exporter import ExcelExporter
from taskflow.task_blocks.end_block import EndBlock
from taskflow.task_blocks.extract_data_block import ExtractDataBlock, Field, TextFieldExtractor
from taskflow.task_blocks.if_block import IfBlock
from taskflow.task_blocks.input_block import InputBlock
from taskflow.task_blocks.loop_block import LoopBlock
from taskflow.task_blocks.loop_type import FixedLoopType
from taskflow.task_blocks.open_page_block import OpenPageBlock
from taskflow.task_blocks.rollback_block import RollbackBlock
from taskflow.task_blocks.start_block import StartBlock
from taskflow.variable_system import VariableType, VariableScope

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


def runoob_test():
    open_page_url = "https://www.runoob.com/"

    control_flow = ControlFlow()

    data_exporter = ExcelExporter(name='data.xlsx')
    field_saver = FieldSaver()
    field_saver.set_data_exporter(data_exporter)

    start_block = StartBlock("start", control_flow.get_context())
    open_page_block = OpenPageBlock("打开网页", open_page_url, control_flow.get_context())

    xpath_list = [
        "/html/body/div[4]/div/div[2]/div[1]/a[1]",
        "/html/body/div[4]/div/div[2]/div[1]/a[2]",
        "/html/body/div[4]/div/div[2]/div[1]/a[3]",
        "/html/body/div[4]/div/div[2]/div[1]/a[4]",
        "/html/body/div[4]/div/div[2]/div[1]/a[5]",
        "/html/body/div[4]/div/div[2]/div[1]/a[6]",
        "/html/body/div[4]/div/div[2]/div[1]/a[7]",
    ]
    loop_block = LoopBlock("循环获取教程列表", control_flow.get_context())
    fixed_loop_type = FixedLoopType("固定循环", xpath_list)
    loop_block.set_loop_type(fixed_loop_type)

    extract_block2 = ExtractDataBlock("提取数据", control_flow.get_context())
    text_field_extractor = TextFieldExtractor("文本数据提取")
    field1 = Field("网站", "/html/body/div[4]/div/div[2]/div[1]/h2").set_extractor(text_field_extractor)
    extract_block2.add_field_list([field1])
    extract_block2.set_field_observer(field_saver)

    extract_block = ExtractDataBlock("提取数据", control_flow.get_context())
    extract_block.set_use_relative_xpath(True)
    extract_block.set_field_observer(field_saver)

    text_field_extractor = TextFieldExtractor("文本数据提取")
    field1 = Field("标题", "/h4").set_extractor(text_field_extractor)
    field2 = Field("内容", "/strong").set_extractor(text_field_extractor)
    extract_block.add_field_list([field1, field2])
    loop_block.add_inner(extract_block)

    end_block = EndBlock("结束", control_flow.get_context())
    end_block.observe(field_saver.save)

    start_block.set_next_block(open_page_block)\
        .set_next_block(extract_block2)\
        .set_next_block(loop_block)\
        .set_next_block(end_block)

    control_flow.set_start_block(start_block)
    control_flow.run()
    input("输入任何字符按回车后关闭浏览器")


def runoob_if_test():
    open_page_url = "https://www.runoob.com/"

    control_flow = ControlFlow()

    start_block = StartBlock("start", control_flow.get_context())
    open_page_block = OpenPageBlock("打开网页", open_page_url, control_flow.get_context())

    xpath_list = [
        "/html/body/div[4]/div/div[2]/div[1]/a[1]",
        "/html/body/div[4]/div/div[2]/div[1]/a[2]",
        "/html/body/div[4]/div/div[2]/div[1]/a[3]",
        "/html/body/div[4]/div/div[2]/div[1]/a[4]",
        "/html/body/div[4]/div/div[2]/div[1]/a[5]",
        "/html/body/div[4]/div/div[2]/div[1]/a[6]",
        "/html/body/div[4]/div/div[2]/div[1]/a[7]",
    ]
    loop_block = LoopBlock("循环获取教程列表", control_flow.get_context())
    fixed_loop_type = FixedLoopType("固定循环", xpath_list)
    loop_block.set_loop_type(fixed_loop_type)

    if_block = IfBlock("判断是否为CSS教程", control_flow.get_context())
    js_condition_block = ExecJavaScriptConditionBlock("执行脚本-判断是否为CSS教程", control_flow.get_context(),
                                 "return arguments[0].innerText.includes('CSS')")
    pass_condition_block = PassConditionBlock("无条件", control_flow.get_context())
    if_block.add_condition(js_condition_block)
    if_block.add_condition(pass_condition_block)

    extract_block = ExtractDataBlock("提取数据", control_flow.get_context())
    extract_block.set_use_relative_xpath(True)
    text_field_extractor = TextFieldExtractor("标题")
    field1 = Field("标题", "/h4").set_extractor(text_field_extractor)
    field2 = Field("内容", "/strong").set_extractor(text_field_extractor)
    extract_block.add_field_list([field1, field2])
    js_condition_block.add_inner(extract_block)

    loop_block.add_inner(if_block)

    end_block = EndBlock("结束", control_flow.get_context())

    start_block.set_next_block(open_page_block).set_next_block(loop_block).set_next_block(end_block)

    control_flow.set_start_block(start_block)
    control_flow.run()
    input("输入任何字符按回车后关闭浏览器")


def click_element_test():
    open_page_url = "https://www.runoob.com/"

    control_flow = ControlFlow()

    start_block = StartBlock("开始", control_flow.get_context())
    open_page_block = OpenPageBlock("打开网页", open_page_url, control_flow.get_context())
    click_block = ClickElementBlock("点击按钮", control_flow.get_context(), "/html/body/div[2]/div/div/ul/li[3]/a")
    end_block = EndBlock("结束", control_flow.get_context())

    start_block.set_next_block(open_page_block).set_next_block(click_block).set_next_block(end_block)

    control_flow.set_start_block(start_block)
    control_flow.run()
    input("输入任何字符按回车后关闭浏览器")

def relative_click_element_test():
    open_page_url = "https://www.runoob.com/"

    control_flow = ControlFlow()

    start_block = StartBlock("start", control_flow.get_context())
    open_page_block = OpenPageBlock("打开网页", open_page_url, control_flow.get_context())

    xpath_list = [
        "/html/body/div[4]/div/div[2]/div[1]/a[1]",
        "/html/body/div[4]/div/div[2]/div[1]/a[2]",
        "/html/body/div[4]/div/div[2]/div[1]/a[3]",
        "/html/body/div[4]/div/div[2]/div[1]/a[4]",
        "/html/body/div[4]/div/div[2]/div[1]/a[5]",
        "/html/body/div[4]/div/div[2]/div[1]/a[6]",
        "/html/body/div[4]/div/div[2]/div[1]/a[7]",
    ]
    loop_block = LoopBlock("循环点击链接", control_flow.get_context())
    fixed_loop_type = FixedLoopType("固定循环", xpath_list)
    loop_block.set_loop_type(fixed_loop_type)

    click_block = ClickElementBlock("点击按钮", control_flow.get_context(), "")
    click_block.set_use_relative_xpath(True)
    rollback_block = RollbackBlock("回退", control_flow.get_context())
    click_block.set_next_block(rollback_block)

    loop_block.add_inner(click_block)

    end_block = EndBlock("结束", control_flow.get_context())

    start_block.set_next_block(open_page_block).set_next_block(loop_block).set_next_block(end_block)

    control_flow.set_start_block(start_block)
    control_flow.run()
    input("输入任何字符按回车后关闭浏览器")

def rollback_test():
    open_page_url = "https://www.runoob.com/"

    control_flow = ControlFlow()

    start_block = StartBlock("start", control_flow.get_context())
    open_page_block = OpenPageBlock("打开网页", open_page_url, control_flow.get_context())

    click_block = ClickElementBlock("点击按钮", control_flow.get_context(), "/html/body/div[4]/div/div[2]/div[2]/a[1]")
    click_block2 = ClickElementBlock("点击按钮", control_flow.get_context(), "/html/body/div[4]/div/div[1]/div/div[2]/div/a[6]")
    click_block3 = ClickElementBlock("点击按钮", control_flow.get_context(),
                                     "/html/body/div[4]/div/div[2]/div/div[3]/div/div[1]/a")
    click_block4 = ClickElementBlock("点击按钮", control_flow.get_context(),
                                     "/html/body/div[1]/div/div[1]/div/div[1]/button[3]")
    rollback_block = RollbackBlock("回退", control_flow.get_context())
    rollback2_block = RollbackBlock("回退", control_flow.get_context())
    rollback3_block = RollbackBlock("回退", control_flow.get_context())
    rollback4_block = RollbackBlock("回退", control_flow.get_context())

    end_block = EndBlock("结束", control_flow.get_context())

    start_block.set_next_block(open_page_block)\
        .set_next_block(click_block)\
        .set_next_block(click_block2) \
        .set_next_block(click_block3) \
        .set_next_block(click_block4) \
        .set_next_block(rollback_block) \
        .set_next_block(rollback2_block) \
        .set_next_block(rollback3_block) \
        .set_next_block(rollback4_block) \
        .set_next_block(end_block)

    control_flow.set_start_block(start_block)
    control_flow.run()
    input("输入任何字符按回车后关闭浏览器")

def input_test():
    open_page_url = "https://www.jd.com/"

    control_flow = ControlFlow()

    start_block = StartBlock("start", control_flow.get_context())
    open_page_block = OpenPageBlock("打开网页", open_page_url, control_flow.get_context())

    input_block = InputBlock("输入", control_flow.get_context(),
                             "/html/body/div[1]/div[4]/div/div[2]/div/div[2]/input", "笔记本电脑")

    end_block = EndBlock("结束", control_flow.get_context())

    start_block.set_next_block(open_page_block).set_next_block(input_block).set_next_block(end_block)

    control_flow.set_start_block(start_block)
    control_flow.run()
    input("输入任何字符按回车后关闭浏览器") 

def factory_test():
    control_flow = ControlFlow()
    factory = BlockFactory(control_flow.get_context())
    block = factory.create_block("ClickElementBlock", {
        "name": "点击按钮",
        "xpath": "/html/body/div[4]/div/div[2]/div[2]/a[1]",
        "need_track": False
    })
    print(block)


def json_flow_test():
    control_flow = JsonFlowParser("./test/relative_click_element_test.json").parse()
    control_flow.run()
    input("输入任何字符按回车后关闭浏览器")

def coordinate_click_test():
    control_flow = JsonFlowParser("./test/coordinate_click_test.json").parse(debug_mode=True)
    control_flow.run()
    input("输入任何字符按回车后关闭浏览器")

def json_variable_test():
    """使用JSON配置测试变量系统"""
    # 加载并解析JSON流程
    control_flow = JsonFlowParser("./test/variable_system_test.json").parse(debug_mode=True)
    
    # 获取初始变量值
    context = control_flow.get_context()
    search_keyword = context.get_variable_value("search_keyword")
    print(f"初始搜索关键词: {search_keyword}")
    
    # 运行流程
    print("开始执行JSON变量系统测试...")
    control_flow.run()
    
    # 获取执行结果
    results = context.get_variable_value("results")
    result_count = context.get_variable_value("result_count")
    
    print(f"\n搜索结果数量: {result_count}")
    print("搜索结果:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['name']}: {result['value']}")
    
    input("输入任何字符按回车后关闭浏览器")


if __name__ == '__main__':
    # runoob_test()
    # runoob_if_test()
    # click_element_test()
    # relative_click_element_test()
    # rollback_test()
    # input_test()
    # factory_test()
    # json_flow_test()
    # coordinate_click_test()
    json_variable_test()  # 测试JSON变量系统
    
