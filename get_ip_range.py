# -*- coding: utf-8 -*-
# @Time : 2025/12/14 21:45
# @Author : tmac
# @File : get_ip_range.py
from fastmcp import FastMCP
import ipaddress
import json

# 创建MCP服务器
mcp = FastMCP("ip_range_calculator")


@mcp.tool(
    name="get_ip_range",
    description="输入一个带掩码的IP地址（如 192.168.1.0/24），返回该网段所有有效的IP地址范围（排除网络地址和广播地址）。结果以JSON格式返回。"
)
def get_ip_range(ip_with_cidr: str) -> str:
    """
    计算IP地址范围

    Args:
        ip_with_cidr: 带CIDR掩码的IP地址，例如 "192.168.1.0/24" 或 "10.0.0.0/16"

    Returns:
        JSON格式的字符串，包含网络地址、广播地址、可用IP范围和可用IP数量
    """
    try:
        # 解析网络地址
        network = ipaddress.ip_network(ip_with_cidr, strict=False)

        # 获取基本信息
        network_address = str(network.network_address)
        broadcast_address = str(network.broadcast_address)
        netmask = str(network.netmask)
        cidr_notation = f"/{network.prefixlen}"

        # 计算可用IP范围（排除网络地址和广播地址）
        if network.prefixlen >= 31:  # /31 和 /32 网络特殊处理
            # /31 网络用于点对点链接，没有广播地址
            # /32 网络只有一个地址
            if network.prefixlen == 32:
                usable_ips = [str(network.network_address)]
                first_usable = last_usable = str(network.network_address)
                total_usable = 1
            else:  # /31
                all_hosts = list(network.hosts())
                usable_ips = [str(ip) for ip in all_hosts]
                first_usable = str(network.network_address)
                last_usable = str(network.broadcast_address)
                total_usable = 2
        else:
            # 标准网络：排除网络地址和广播地址
            all_hosts = list(network.hosts())
            usable_ips = [str(ip) for ip in all_hosts]
            first_usable = str(all_hosts[0]) if all_hosts else "N/A"
            last_usable = str(all_hosts[-1]) if all_hosts else "N/A"
            total_usable = len(all_hosts)

        # 构建结果字典
        result = {
            "input": ip_with_cidr,
            "network_info": {
                "network_address": network_address,
                "broadcast_address": broadcast_address,
                "netmask": netmask,
                "cidr_notation": cidr_notation,
                "prefix_length": network.prefixlen
            },
            "usable_ip_range": {
                "first_usable_ip": first_usable,
                "last_usable_ip": last_usable,
                "total_usable_ips": total_usable
            },
            "all_usable_ips": usable_ips if total_usable <= 100 else f"共 {total_usable} 个IP，前100个已显示" + str(
                usable_ips[:100])
        }

        # 转换为JSON格式并返回
        return json.dumps(result, indent=2, ensure_ascii=False)

    except ValueError as e:
        # 处理无效输入
        error_result = {
            "error": "无效的IP地址格式",
            "message": str(e),
            "input": ip_with_cidr,
            "valid_examples": [
                "192.168.1.0/24",
                "10.0.0.0/16",
                "172.16.0.0/12",
                "192.168.1.100/28"
            ]
        }
        return json.dumps(error_result, indent=2, ensure_ascii=False)


@mcp.tool(
    name="get_ip_range_summary",
    description="输入一个带掩码的IP地址，只返回可用的IP范围摘要（不显示所有IP列表）。"
)
def get_ip_range_summary(ip_with_cidr: str) -> str:
    """简化版本，只返回范围摘要"""
    try:
        network = ipaddress.ip_network(ip_with_cidr, strict=False)

        # 计算可用IP数量
        if network.prefixlen == 32:
            total_usable = 1
            first_usable = last_usable = str(network.network_address)
        elif network.prefixlen == 31:
            total_usable = 2
            first_usable = str(network.network_address)
            last_usable = str(network.broadcast_address)
        else:
            total_usable = network.num_addresses - 2
            first_usable = str(list(network.hosts())[0])
            last_usable = str(list(network.hosts())[-1])

        result = {
            "input": ip_with_cidr,
            "network": str(network.network_address),
            "netmask": str(network.netmask),
            "cidr": f"/{network.prefixlen}",
            "usable_range": f"{first_usable} - {last_usable}",
            "total_ips": network.num_addresses,
            "usable_ips": total_usable,
            "broadcast": str(network.broadcast_address)
        }

        return json.dumps(result, indent=2, ensure_ascii=False)

    except ValueError as e:
        return json.dumps({"error": str(e), "input": ip_with_cidr}, indent=2)


if __name__ == "__main__":
    # 启动服务器
    print("IP范围计算器 MCP 服务器启动中...")
    print("可用工具:")
    print("1. get_ip_range - 输入IP/掩码，返回完整的IP范围信息")
    print("2. get_ip_range_summary - 输入IP/掩码，返回简化的范围摘要")
    print(f"服务地址: http://127.0.0.1:8000")

    mcp.run(transport="http", host="0.0.0.0", port=8000)
