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


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
	"Cookie": "gamecenter_wiki_UserName=12142849; gamecenter_wiki__session=1fhve4lk1bkidm9bgeiqslbjjv5rkqg8; gamecenter_wiki_UserID=254622; gamecenter_wiki_UserGroups=bilibili; SESSDATA=01d9e7d4%2C1786726177%2C0e098%2A22CjD2bbGlRVL_acGJ-FoWCd-MH6HEahrQsTErQPzYp_V6Do51ziRMvqUESeXhubErPGoSVkdSTDl6c3M2UlhpNlU4UFdhYm1RZHVjUEQxX3BOUExRUnN5TGdUZzJMdjk4dVBzMWdBU2RmbzY3WmRUODA1QzE2MnhTaTZmMWtHaVp3QWRWUnBQV29RIIEC; bili_jct=53abd88452b0df97a70b31550d3406ba; DedeUserID=12142849; DedeUserID__ckMd5=5004403a40802b2e; sid=nhjzrh4z; b_nut=1771488904; buvid3=E1E2B94B-4981-7E5B-E54F-033D8ECE35A505033infoc; buvid_fp=2e934c22b42a6595436063c8f8d3e45b; Hm_lvt_e61bc5e4df128a1dc4db0bb30558ebe4=1773495587; Hm_lvt_cb50e488eca598646f26b3bf09b83ada=1784287919,1784287919; bsource=search_bing; buvid4=EE028B61-EAC4-F188-1CBB-22CF8DE03EB948648-026071821-zzY4myeXOxLljlBEzmLA8g%3D%3D; HMACCOUNT=10CE10543CD8E618; Hm_lpvt_cb50e488eca598646f26b3bf09b83ada=1785004851; b_lsid=5FE88482_19F9A9481D0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Sec-Ch-Ua": '"Chromium";v="125", "Microsoft Edge";v="125", "Not.A/Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

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
			async with session.get(url, headers=headers) as resp:
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
						async with session.get(url, headers=headers) as resp:
							web = await resp.content.read()
							context = BeautifulSoup(web)
							logger.debug(f"查询技能网页内容={context}")
							cards = context.find_all(style="position:relative;width:100px;margin:3px;")
							logger.debug(f"查询技能网页卡片内容={cards}")
							skill_data = context.find(class_="wikitable")
							logger.debug(f"查询技能网页技能数据={skill_data}")
							skill_info = skill_data and skill_data.find_all("td")
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
			await wait_for_selection(event)
			# try:
			# 	await wait_for_selection(event)
			# except Exception as e:
			# 	logger.error(f"等待技能选择时发生错误: {e}")
			# 	yield event.plain_result("查询技能失败  未找到该技能")
			# finally:
			# 	event.stop_event()
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
			async with session.get(url, params=params, headers=headers, timeout=10) as resp:
				if resp.status != 200:
					error_text = await resp.text()
					logger.error(f"请求技能列表失败，状态码: {resp.status}, 错误信息: {error_text}")
					return []
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
