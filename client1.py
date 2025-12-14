# -*- coding: utf-8 -*-
# @Time : 2025/12/14 19:58
# @Author : tmac
# @File : client1.py
import asyncio

from fastmcp import Client

client = Client("http://127.0.0.1:8000/mcp")

async def call_tool(name:str):
    async with client:
        response = await client.call_tool("great",{"name":name})
        print(response)


asyncio.run(call_tool("TMAC"))
