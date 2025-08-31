from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from bs4 import BeautifulSoup
import aiohttp
import astrbot.api.message_components as Comp
from astrbot.api.message_components import Node
# import urllib
from urllib.parse import quote


# 暂时用着  不行再换
MALI_COOKIE = "testcookie=1; buvid4=5E5E8448-72F4-D5F6-FCC0-2132E1341FBD95024-024050507-xhy32Epe3ibVFcwg2NBESQ%3D%3D; enable_web_push=DISABLE; DedeUserID=12142849; DedeUserID__ckMd5=5004403a40802b2e; buvid_fp_plain=undefined; CURRENT_QUALITY=80; is-2022-channel=1; enable_feed_channel=ENABLE; buvid3=26D9EF48-8248-BB7A-3294-9F451DDB043406532infoc; b_nut=1746430607; _uuid=32AB8EAB-A618-10B93-31104-2F58FC101768610006infoc; fingerprint=67e5fcc28e95af0717e0fa1f1f75058b; buvid_fp=67e5fcc28e95af0717e0fa1f1f75058b; rpdid=|(um||~)JJ|k0J'u~Rml~Rm)Y; LIVE_BUVID=AUTO6517498133009814; hit-dyn-v2=1; header_theme_version=OPEN; theme-tip-show=SHOWED; theme-avatar-tip-show=SHOWED; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTY4MTM1NjAsImlhdCI6MTc1NjU1NDMwMCwicGx0IjotMX0.prlZ2Y4MdSBfkzwmKQMZd_P9kglgxyZJhFrTRGbgi5s; bili_ticket_expires=1756813500; SESSDATA=d1fb959a%2C1772114879%2Ca16b8%2A81CjCyJPfdBHBFcQp6pm2QTtTEiNR0gj4-DEoZYrCwiVtZlN2MEFnRUhmT_1guncTs0iYSVlozbG8zdmpfSU41dzg2azdscEFwcUxablNlYlRzNFRTd2o1Mm5HdVFaYVZybDBIS2ozQzdxQ0JRR0NXVUV5V3gyM1BuM3pWZHE3cnBOQnVpZnRjbzlRIIEC; bili_jct=f73b755109cf29337cc3243c11b63986; sid=7501nseu; timeMachine=0; PVID=3; home_feed_column=5; browser_resolution=2048-1111; bp_t_offset_12142849=1106967931520024576; CURRENT_FNVAL=16; b_lsid=E6423810C_198FE4D6ECC"


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
                skill_data = context.find(class_="wikitable")
                skill_info = skill_data.find_all("td")
                chain.append(Comp.Plain(text=f"类型={skill_info[2].string}代码={skill_info[5].string}描述={skill_info[6].string}类型={skill_info[7].string}数值={skill_info[8].string}时长={skill_info[9].string}"))
                for card in cards:
                    card_img = card.contents[0].contents[0]
                    chain.append(Comp.Image.fromURL(card_img.attrs.get("src")))
        if len(chain) == 0:
            yield event.plain_result("查询技能失败  未找到该技能")
        else:
            node = Node(chain)
            yield event.chain_result([node])

    @filter.command("query")
    async def query_stud(self, event: AstrMessageEvent):
        pass

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        logger.warning("测试插件销毁!!!!!!!!!!!!!!!!!!!")
