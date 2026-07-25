from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from bs4 import BeautifulSoup
import aiohttp
import astrbot.api.message_components as Comp
from astrbot.api.message_components import Node
from astrbot.core.utils.session_waiter import (
    session_waiter,
    SessionController,
)
# import urllib
from urllib.parse import quote


class UmaPlugins(Star):
	def __init__(self, context: Context):
		super().__init__(context)
		self.cur_select_keyworld = None

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
				if cards:
					skill_data = context.find(class_="wikitable")
					skill_info = skill_data and skill_data.find_all("td")
					if skill_info:
						chain.append(Comp.Plain(text=f"类型={skill_info[2].string}代码={skill_info[5].string}描述={skill_info[6].string}类型={skill_info[7].string}数值={skill_info[8].string}时长={skill_info[9].string}"))
						for card in cards:
							card_img = card.contents[0].contents[0]
							chain.append(Comp.Image.fromURL(card_img.attrs.get("src")))
		if len(chain) == 0:
			# 没有精确匹配上  尝试搜全局
			# yield event.plain_result("查询技能失败  未找到该技能")
			skill_list = await self.get_skill_name_list(skill_name)
			if len(skill_list) == 0:
				yield event.plain_result("查询技能失败  未找到技能")
			chain.append(Comp.Plain(text="未找到技能  可能是技能名不完整  下面是模糊匹配到的技能列表  输入序号查询对应技能"))
			for index, skill in enumerate(skill_list):
				chain.append(Comp.Plain(text=f"{index}. {skill}"))
			yield event.chain_result([Node(chain)])

			@session_waiter(timeout=60, record_history_chains=False)
			async def wait_for_selection(controller: SessionController, event: AstrMessageEvent):
				idiom = event.message_str
				if idiom.isdigit() and 0 <= int(idiom) < len(skill_list):
					skill_name = skill_list[int(idiom)]
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
						message_result = event.make_result()
						message_result.chain = [Comp.Plain(text="查询技能失败  未找到该技能")]
						await event.send(message_result)
					else:
						node = Node(chain)
						await event.send(event.chain_result([node]))

					controller.stop()
			try:
				await wait_for_selection(event)
			except:
				yield event.plain_result("查询技能失败  未找到该技能")
			finally:
				event.stop_event()
		else:
			node = Node(chain)
			yield event.chain_result([node])

	async def get_skill_name_list(self, name=""):
		url = 'https://wiki.biligame.com/umamusume/api.php'
		query = f'[[分类:简中技能]][[简中名::~*{name}*]]|?ID|?简中名|?稀有度|?条件限制|?图标颜色|?简中技能描述|?简中技能类型|?简中技能数值|?简中持续时间|?评价分|?共需技能PT|?PT评价比|?简中触发条件'
		params = {
			'action': 'ask',
			'format': 'json',
			'query': query,
		}

		async with aiohttp.ClientSession() as session:
			data = {}
			async with session.get(url, params=params, timeout=10) as resp:
				resp.raise_for_status()
				data = await resp.json()

			results: dict = data.get('query', {}).get('results', {})
			skills = []
			for item in results.values():
				printouts = item.get('printouts', {})
				names = printouts.get('简中名', [])
				if names:
					skills.append(names[0])
			return skills

	@filter.command("query")
	async def query_stud(self, event: AstrMessageEvent):
		pass

	async def terminate(self):
		"""可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
		logger.warning("测试插件销毁!!!!!!!!!!!!!!!!!!!")
		self.cur_select_keyworld = None
