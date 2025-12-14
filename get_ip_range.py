# -*- coding: utf-8 -*-
# @Time : 2025/12/14 21:45
# @Author : tmac
# @File : get_ip_range.py
from fastmcp import FastMCP
import ipaddress
import json
from typing import Dict, List, Any
from datetime import datetime

# 创建MCP服务器
mcp = FastMCP("ip_range_calculator")


def format_json(data: Dict[str, Any], indent: int = 2, sort_keys: bool = True) -> str:
    """格式化JSON输出，使其更美观易读"""
    return json.dumps(
        data,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=False,
        separators=(',', ': ')
    )


@mcp.tool(
    name="get_ip_range",
    description="输入一个带掩码的IP地址（如 192.168.1.0/24），返回该网段所有有效的IP地址范围和详细信息。"
)
def get_ip_range(ip_with_cidr: str, show_all_ips: bool = False) -> str:
    """
    计算IP地址范围 - 增强版

    Args:
        ip_with_cidr: 带CIDR掩码的IP地址，例如 "192.168.1.0/24"
        show_all_ips: 是否显示所有IP列表（对于大网络可能影响性能）

    Returns:
        JSON格式的字符串，包含详细的网络信息
    """
    try:
        # 记录开始时间
        start_time = datetime.now()

        # 解析网络地址
        network = ipaddress.ip_network(ip_with_cidr, strict=False)

        # 获取基本信息
        network_address = str(network.network_address)
        broadcast_address = str(network.broadcast_address)
        netmask = str(network.netmask)
        cidr_notation = f"/{network.prefixlen}"
        total_addresses = network.num_addresses
        wildcard_mask = str(network.hostmask)

        # 计算网络类别和类型
        network_class = get_network_class(network)
        network_type = get_network_type(network.prefixlen)
        is_private = network.is_private
        is_global = network.is_global
        is_reserved = network.is_reserved

        # 计算可用IP范围
        if network.prefixlen == 32:
            # /32 网络：只有一个地址
            total_usable = 1
            first_usable = last_usable = network_address
            usable_ips = [network_address]
        elif network.prefixlen == 31:
            # /31 网络：点对点链接，两个地址都可用
            total_usable = 2
            first_usable = network_address
            last_usable = broadcast_address
            usable_ips = [network_address, broadcast_address]
        else:
            # 标准网络：排除网络地址和广播地址
            total_usable = total_addresses - 2
            hosts = list(network.hosts())
            first_usable = str(hosts[0]) if hosts else "N/A"
            last_usable = str(hosts[-1]) if hosts else "N/A"
            usable_ips = [str(ip) for ip in hosts]

        # 计算二进制表示
        network_binary = '.'.join([format(int(octet), '08b') for octet in network_address.split('.')])
        mask_binary = '.'.join([format(int(octet), '08b') for octet in netmask.split('.')])

        # 计算下一个网络
        try:
            next_network = str(network.network_address + network.num_addresses)
        except:
            next_network = "N/A"

        # 计算子网划分可能性
        subnet_possibilities = []
        if network.prefixlen < 30:
            for new_prefix in range(network.prefixlen + 1, min(31, network.prefixlen + 5)):
                subnet_count = 2 ** (new_prefix - network.prefixlen)
                subnet_possibilities.append({
                    "new_prefix": new_prefix,
                    "subnet_count": subnet_count,
                    "hosts_per_subnet": (2 ** (32 - new_prefix)) - 2 if new_prefix < 31 else 2
                })

        # 构建详细结果字典
        result = {
            "metadata": {
                "timestamp": start_time.isoformat(),
                "processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                "tool": "get_ip_range",
                "version": "2.0"
            },
            "input": {
                "original": ip_with_cidr,
                "normalized": str(network)
            },
            "network_summary": {
                "network_address": network_address,
                "broadcast_address": broadcast_address,
                "netmask": netmask,
                "wildcard_mask": wildcard_mask,
                "cidr_notation": cidr_notation,
                "prefix_length": network.prefixlen,
                "total_addresses": total_addresses,
                "network_class": network_class,
                "network_type": network_type
            },
            "address_properties": {
                "is_private": is_private,
                "is_global": is_global,
                "is_reserved": is_reserved,
                "is_multicast": network.is_multicast,
                "is_loopback": network.is_loopback,
                "is_link_local": network.is_link_local
            },
            "binary_representation": {
                "network_binary": network_binary,
                "mask_binary": mask_binary,
                "network_hex": network.network_address.exploded,
                "mask_hex": network.netmask.exploded
            },
            "usable_ip_range": {
                "first_usable_ip": first_usable,
                "last_usable_ip": last_usable,
                "total_usable_ips": total_usable,
                "percentage_usable": round((total_usable / total_addresses) * 100, 2) if total_addresses > 0 else 0
            },
            "network_calculations": {
                "next_network_address": next_network,
                "network_size_bits": 32 - network.prefixlen,
                "host_bits": 32 - network.prefixlen,
                "network_bits": network.prefixlen
            },
            "subnetting_info": {
                "possible_subnets": subnet_possibilities,
                "max_subnets": 2 ** (30 - network.prefixlen) if network.prefixlen < 30 else 1,
                "recommended_prefix": min(28, network.prefixlen + 4)
            }
        }

        # 添加IP列表（根据参数和网络大小决定）
        if show_all_ips and total_usable <= 1000:
            result["all_usable_ips"] = {
                "count": total_usable,
                "list": usable_ips
            }
        elif show_all_ips:
            result["all_usable_ips"] = {
                "count": total_usable,
                "note": f"网络过大，显示所有{total_usable}个IP可能影响性能",
                "first_50": usable_ips[:50],
                "last_50": usable_ips[-50:],
                "sample_interval": usable_ips[::max(1, total_usable // 20)][:20]
            }
        else:
            result["all_usable_ips"] = {
                "count": total_usable,
                "note": "使用 show_all_ips=true 参数查看完整列表",
                "sample": usable_ips[:10] if total_usable > 10 else usable_ips
            }

        # 添加统计信息
        result["statistics"] = {
            "density_percentage": round((total_usable / 256) * 100, 2) if total_usable <= 256 else 100,
            "estimated_memory_kb": round((total_usable * 15) / 1024, 2),
            "recommended_use": recommend_network_use(network)
        }

        # 添加友好的显示文本
        result["display"] = {
            "summary": f"网络 {network_address}{cidr_notation} ({netmask})",
            "range": f"可用IP范围: {first_usable} - {last_usable}",
            "count": f"可用主机数量: {total_usable}",
            "percentage": f"可用率: {round((total_usable / total_addresses) * 100, 2)}%"
        }

        return format_json(result)

    except ValueError as e:
        # 详细的错误信息
        error_result = {
            "error": {
                "type": "ValueError",
                "message": str(e),
                "suggestion": "请检查IP地址和掩码格式"
            },
            "input": ip_with_cidr,
            "examples": {
                "valid_formats": [
                    "192.168.1.0/24",
                    "10.0.0.0/16",
                    "172.16.0.0/12",
                    "192.168.1.100/28"
                ],
                "common_errors": [
                    "192.168.1.0/33 (掩码不能大于32)",
                    "192.168.1.256/24 (IP地址超出范围)",
                    "192.168.1/24 (IP地址不完整)"
                ]
            },
            "help": {
                "correct_format": "正确格式: A.B.C.D/X (其中 X 是 0-32 的整数)",
                "common_ranges": {
                    "class_a": "10.0.0.0/8 (私有A类)",
                    "class_b": "172.16.0.0/12 (私有B类)",
                    "class_c": "192.168.0.0/16 (私有C类)",
                    "small_networks": "192.168.1.0/24 到 192.168.1.0/30"
                }
            }
        }
        return format_json(error_result)


def get_network_class(network: ipaddress.IPv4Network) -> str:
    """获取网络类别"""
    first_octet = int(str(network.network_address).split('.')[0])

    if first_octet <= 127:
        return "A"
    elif first_octet <= 191:
        return "B"
    elif first_octet <= 223:
        return "C"
    elif first_octet <= 239:
        return "D (组播)"
    else:
        return "E (保留)"


def get_network_type(prefix_len: int) -> str:
    """获取网络类型描述"""
    if prefix_len == 32:
        return "单个主机 (/32)"
    elif prefix_len == 31:
        return "点对点链接 (/31)"
    elif prefix_len >= 30:
        return f"超小型网络 (/{prefix_len})"
    elif prefix_len >= 24:
        return f"小型网络 (/{prefix_len})"
    elif prefix_len >= 16:
        return f"中型网络 (/{prefix_len})"
    elif prefix_len >= 8:
        return f"大型网络 (/{prefix_len})"
    else:
        return f"超大型网络 (/{prefix_len})"


def recommend_network_use(network: ipaddress.IPv4Network) -> Dict[str, str]:
    """推荐网络用途"""
    prefix_len = network.prefixlen

    recommendations = {
        "primary_use": "",
        "typical_scenarios": [],
        "recommended_size": ""
    }

    if prefix_len == 32:
        recommendations["primary_use"] = "单个服务器或设备"
        recommendations["typical_scenarios"] = ["VPN终端", "关键服务器", "网络设备管理IP"]
    elif prefix_len == 31:
        recommendations["primary_use"] = "点对点链接"
        recommendations["typical_scenarios"] = ["路由器间连接", "网络设备直连"]
    elif 30 >= prefix_len >= 29:
        recommendations["primary_use"] = "小型网络"
        recommendations["typical_scenarios"] = ["分支机构", "小型办公室", "服务器集群"]
        recommendations["recommended_size"] = "2-14台主机"
    elif 28 >= prefix_len >= 25:
        recommendations["primary_use"] = "办公网络"
        recommendations["typical_scenarios"] = ["部门网络", "中型办公室", "实验室网络"]
        recommendations["recommended_size"] = "14-254台主机"
    elif 24 >= prefix_len >= 22:
        recommendations["primary_use"] = "园区网络"
        recommendations["typical_scenarios"] = ["校园网", "企业网络", "数据中心"]
        recommendations["recommended_size"] = "254-1022台主机"
    else:
        recommendations["primary_use"] = "大型基础设施"
        recommendations["typical_scenarios"] = ["ISP分配", "大型企业", "云服务提供商"]

    return recommendations


@mcp.tool(
    name="get_ip_range_summary",
    description="输入一个带掩码的IP地址，返回简化的网络信息摘要。"
)
def get_ip_range_summary(ip_with_cidr: str) -> str:
    """简化版本，返回网络信息摘要"""
    try:
        network = ipaddress.ip_network(ip_with_cidr, strict=False)

        # 计算基本信息
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
            "summary": {
                "network": str(network.network_address),
                "netmask": str(network.netmask),
                "cidr": f"/{network.prefixlen}",
                "usable_range": f"{first_usable} - {last_usable}",
                "total_addresses": network.num_addresses,
                "usable_hosts": total_usable,
                "broadcast": str(network.broadcast_address),
                "network_class": get_network_class(network),
                "network_type": get_network_type(network.prefixlen)
            },
            "quick_info": {
                "is_private": network.is_private,
                "is_public": network.is_global,
                "host_bits": 32 - network.prefixlen
            }
        }

        return format_json(result)

    except ValueError as e:
        return format_json({
            "error": str(e),
            "input": ip_with_cidr,
            "help": "请输入有效的CIDR格式，如: 192.168.1.0/24"
        })


@mcp.tool(
    name="validate_ip",
    description="验证IP地址或网络格式的有效性，返回详细信息。"
)
def validate_ip(ip_input: str) -> str:
    """验证IP地址或网络"""
    try:
        # 尝试解析为单个IP
        ip = ipaddress.ip_address(ip_input)

        result = {
            "input": ip_input,
            "type": "single_ip",
            "valid": True,
            "version": ip.version,
            "properties": {
                "is_private": ip.is_private,
                "is_global": ip.is_global,
                "is_reserved": ip.is_reserved,
                "is_multicast": ip.is_multicast if ip.version == 4 else False,
                "is_loopback": ip.is_loopback,
                "is_link_local": ip.is_link_local
            },
            "formats": {
                "decimal": str(ip),
                "binary": '.'.join([format(int(octet), '08b') for octet in str(ip).split('.')]),
                "hex": ip.exploded
            }
        }

        return format_json(result)

    except ValueError:
        try:
            # 尝试解析为网络
            network = ipaddress.ip_network(ip_input, strict=False)

            result = {
                "input": ip_input,
                "type": "network",
                "valid": True,
                "version": network.version,
                "network_info": {
                    "network_address": str(network.network_address),
                    "broadcast_address": str(network.broadcast_address),
                    "netmask": str(network.netmask),
                    "cidr": f"/{network.prefixlen}",
                    "total_addresses": network.num_addresses
                }
            }

            return format_json(result)

        except ValueError as e:
            return format_json({
                "input": ip_input,
                "valid": False,
                "error": str(e),
                "suggestions": [
                    "检查IP地址格式是否正确",
                    "掩码范围应在0-32之间",
                    "示例: 192.168.1.1 或 192.168.1.0/24"
                ]
            })


if __name__ == "__main__":
    # 启动服务器
    print("🌐 IP范围计算器 MCP 服务器启动中...")
    print("=" * 60)
    print("📡 服务地址: http://0.0.0.0:8000")
    print("📡 本地访问: http://127.0.0.1:8000")
    print("=" * 60)
    print("🛠️  可用工具:")
    print("  • get_ip_range - 完整网络分析 (支持 show_all_ips 参数)")
    print("  • get_ip_range_summary - 简化摘要")
    print("  • validate_ip - IP地址验证")
    print("=" * 60)
    print("💡 使用示例:")
    print('  curl -X POST http://127.0.0.1:8000/mcp -H "Content-Type: application/json" \\')
    print('       -d \'{"tool": "get_ip_range", "params": {"ip_with_cidr": "192.168.1.0/24"}}\'')
    print("=" * 60)

    mcp.run(transport="http", host="0.0.0.0", port=8000)
