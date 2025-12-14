# -*- coding: utf-8 -*-
# @Time : 2025/12/14 19:40
# @Author : tmac
# @File : server1.py
from fastmcp import FastMCP
mcp = FastMCP("first_mcp_server")

@mcp.tool
def great(name: str)->str:
    return f"Hello {name}, 欢迎来到我的第一个MCP服务!"

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)
