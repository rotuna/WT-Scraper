import io
import re
import json
import aiohttp
import asyncio
import requests

from bs4 import BeautifulSoup as bs


async def fetch(client, url):
    async with client.get(url) as response:
        return await response


async def get_data(url, s):
    global subwiki_dict
    p = await fetch(s, url)
    soup = bs(p.content, "html.parser")
    data = soup.find_all("script")
    pattern = r"var WTVueData = ({.*);"
    for y in data:
        matches = re.finditer(pattern, str(y.string), re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):
            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1
                data = json.loads(match.group(groupNum))
                subwiki_dict.update(data["subwikiList"])


print("In main loop")
payload = {"email": "user", "password": "pass"}

subwiki_dict = {}

loop = asyncio.get_event_loop()


async def main_async_fun(loop):
    global subwiki_dict
    global payload
    async with aiohttp.ClientSession(loop=loop) as s:
        p = await fetch(s, "https://wt.social/login")
        signin = bs(p.content, "html.parser")
        print(signin.find("meta", {"name": "csrf-token"})["content"])
        payload["_token"] = signin.find("meta", {"name": "csrf-token"})["content"]
        p = s.post("https://wt.social/login", data=payload)
        # print(p.text)
        p = await fetch(s, "https://wt.social//wt")
        soup = bs(p.content, "html.parser")
        data = soup.find_all("script")
        pattern = r"var WTVueData = ({.*);"
        for y in data:
            matches = re.finditer(pattern, str(y.string), re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):
                print(matchNum)
                for groupNum in range(0, len(match.groups())):
                    groupNum = groupNum + 1
                    data = json.loads(match.group(groupNum))
                    subwiki_dict.update(data["subwikiList"])
                    total_pages = data["totalPages"]

        count = 0
        print(total_pages)
        tasks = []
        for page in range(2, total_pages + 1):
            count = count + 1
            tasks.append(
                asyncio.ensure_future(
                    get_data("https://wt.social//wt?pageNo=" + str(page), s)
                )
            )
            if count == total_pages or count % 20 == 0:
                loop.run_until_complete(asyncio.wait(tasks))
                tasks = []
                print(count)

                with io.open("wt_subwiki.json", "w") as outfile:
                    json.dump(subwiki_dict, outfile, ensure_ascii=False)


asyncio.run(main_async_fun(loop))
