# import requests

# # 1. 构造 MediaWiki API 请求
# params = {
#     'action': 'ask',
#     'query': '[[分类:简中技能]][[简中名::~*直线*]]|?ID|?简中名|?稀有度|?条件限制|?图标颜色|?简中技能描述|?简中技能类型|?简中技能数值|?简中持续时间|?评价分|?共需技能PT|?PT评价比|?简中触发条件',
#     'format': 'json',
#     'limit': 50000,  # 确保覆盖所有技能,
#     'headers': {'User-Agent': 'Mozilla/5.0'}
# }

# url = 'https://wiki.biligame.com/umamusume/api.php'
# resp = requests.get(url, params=params)
# data = resp.json()

# # 2. 解析结果
# results = data.get('query', {}).get('results', {})
# skills = []

# print(len(results))
# for key, item in results.items():
#     printouts = item.get('printouts', {})
#     # 提取简中名（可能为空列表）
#     names = printouts.get('简中名', [])
#     if names:
#         name = names[0]  # 取第一个（通常是字符串）
#         skills.append({
#             'name': name,
#             'data': printouts  # 保留所有字段备查
#         })
#         print(name)

# # 3. 筛选“简中名”包含“顺”的技能
# filtered = [s for s in skills if '直线' in s['name']]

# # 4. 输出结果
# print(f"共获取 {len(skills)} 个技能，其中包含“顺”的有 {len(filtered)} 个：\n")
# for skill in filtered:
#     print(f"技能名：{skill['name']}")
#     # 可选：打印其他信息
#     print(f"  描述：{skill['data'].get('简中技能描述', [''])[0]}")
#     print(f"  稀有度：{skill['data'].get('稀有度', [''])[0]}")
#     print("-" * 40)
	


import asyncio
import aiohttp

BASE_URL = 'https://wiki.biligame.com/umamusume/api.php'

# 关键：在查询中添加 [[简中名::~*顺*]] 实现模糊匹配
# QUERY = '[[分类:简中技能]][[简中名::~*顺*]]|?ID|?简中名|?稀有度|?条件限制|?图标颜色|?简中技能描述|?简中技能类型|?简中技能数值|?简中持续时间|?评价分|?共需技能PT|?PT评价比|?简中触发条件'
QUERY = '[[分类:简中技能]][[简中名::~*{}*]]|?ID|?简中名|?稀有度|?条件限制|?图标颜色|?简中技能描述|?简中技能类型|?简中技能数值|?简中持续时间|?评价分|?共需技能PT|?PT评价比|?简中触发条件'.format("顺")

async def fetch_skills_with_keyword():
	params = {
		'action': 'ask',
		'format': 'json',
		'query': QUERY,
	}

	async with aiohttp.ClientSession() as session:
		async with session.get(BASE_URL, params=params, timeout=10) as resp:
			resp.raise_for_status()
			data = await resp.json()

	results = data.get('query', {}).get('results', {})
	skills = []
	for key, item in results.items():
		printouts = item.get('printouts', {})
		names = printouts.get('简中名', [])
		if names:
			skills.append({
				'name': names[0],
				'data': printouts
			})
	return skills

async def main():
	skills = await fetch_skills_with_keyword()
	print(f"找到 {len(skills)} 个简中名包含“顺”的技能：")
	for s in skills:
		print(f"  - {s['name']}")
		# 可选：打印描述
		desc = s['data'].get('简中技能描述', [''])[0]
		if desc:
			print(f"    描述：{desc}")

if __name__ == '__main__':
	asyncio.run(main())