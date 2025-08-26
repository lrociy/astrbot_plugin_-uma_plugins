from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from bs4 import BeautifulSoup
import aiohttp
import astrbot.api.message_components as Comp
from astrbot.api.message_components import Node
# import urllib
from urllib.parse import quote


class UmaPlugins(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        logger.warning("测试插件启动!!!!!!!!")

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("uma_test")
    async def uma_test(self, event: AstrMessageEvent):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!") # 发送一条纯文本消息

    @filter.command("skill")
    async def query_skill(self, event: AstrMessageEvent):
        message_str = event.message_str
        params = message_str.split(" ")
        if len(params) != 2:
            yield event.plain_result("查询技能失败  参数格式不正确  应为/skill skill_name")
        skill_name = params[-1]
        chain = []
        url = "https://wiki.biligame.com/umamusume/" + quote(f"简/{skill_name}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                web = await resp.content.read()
                context = BeautifulSoup(web)
                cards = context.find_all(style="position:relative;width:100px;margin:3px;")
                for card in cards:
                    card_img = card.contents[0].contents[0]
                    chain.append(Comp.Image.fromURL(card_img.attrs.get("src")))
        if len(chain) == 0:
            yield event.plain_result("查询技能失败  未找到该技能")
        else:
            node = Node(chain)
            yield event.chain_result([node])

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        logger.warning("测试插件销毁!!!!!!!!!!!!!!!!!!!")
