#!/usr/bin/env python3
"""将墨鱼上游配置与个人分流策略合成为圈 X 配置。"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


UPSTREAM_URL = "https://ddgksf2013.top/Profile/QuantumultX.conf"
WECHAT_RULE_URL = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/WeChat/WeChat.list"
SECTION_RE = re.compile(r"^\[([^\]]+)\]\s*$")
SECTION_NAMES = {"general", "task_local", "rewrite_local", "rewrite_remote", "server_local", "server_remote", "dns", "policy", "filter_remote", "filter_local", "http_backend", "mitm"}
PERSONAL_OVERRIDE_SECTIONS = {"policy"}
OFFICIAL_SERVER_REMOTE = """[server_remote]

# > 墨鱼官方临时订阅
https://raw.githubusercontent.com/Ruk1ng001/freeSub/main/clash.yaml#delreg=.*&rename=@tg%40ddgksf2021-+@num-$index7, tag=🐟临时使用, update-interval=3600, opt-parser=true, enabled=true
"""

# 官方分流使用官方策略组名称。合并到个人策略组时必须改成实际存在的名称。
POLICY_MAP = {
    "声田音乐": "🎵Spotify",
    "国际媒体": "🚀 节点选择",
    "哔哩哔哩": "direct",
    "苹果服务": "direct",
    "全球加速": "🚀 节点选择",
    "兜底分流": "🛟 漏网之鱼",
}


def split_sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    matches = list(re.finditer(r"(?m)^\[([^\]]+)\]\s*$", text))
    if not matches:
        raise ValueError("配置中没有圈 X 配置分区")
    prefix = text[: matches[0].start()]
    sections = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((match.group(1), text[match.start():end]))
    return prefix, sections


def meaningful(section: str) -> bool:
    return any(line.strip() and not line.lstrip().startswith(("#", ";")) for line in section.splitlines()[1:])


def body_lines(section: str) -> list[str]:
    """提取分区标题下实际生效的配置行，忽略注释和空行。"""
    return [
        line.strip()
        for line in section.splitlines()[1:]
        if line.strip() and not line.lstrip().startswith(("#", ";"))
    ]


def resource_url(line: str) -> str:
    return line.split(",", 1)[0].strip()


def map_official_policy(line: str) -> str:
    """将官方规则资源引用的策略映射到个人策略组。"""
    match = re.search(r"force-policy=([^,]+)", line)
    if not match:
        return line
    policy = match.group(1).strip()
    if "ddgksf2013.top/filter/Ai.yaml" in line:
        replacement = "🤖 AI平台"
    elif policy == "美国节点":
        replacement = "🇺🇸 美国节点"
    elif policy == "reject":
        replacement = "🛡️ 广告拦截"
    else:
        replacement = POLICY_MAP.get(policy, policy)
    return line[:match.start(1)] + replacement + line[match.end(1):]


def merge_filter_remote(official: str, personal: str) -> str:
    """合并远程规则；网址相同时优先采用个人配置。"""
    personal_lines = body_lines(personal)
    personal_urls = {resource_url(line) for line in personal_lines}
    priority_ai = [line for line in personal_lines if "force-policy=🤖 AI平台" in line]
    personal_lines = [line for line in personal_lines if line not in priority_ai]
    # 微信图片直连规则放在最前，避免广告规则或宽泛代理规则误匹配。
    priority_direct = [
        line for line in personal_lines if resource_url(line) == WECHAT_RULE_URL
    ]
    personal_lines = [
        line for line in personal_lines if resource_url(line) != WECHAT_RULE_URL
    ]
    official_lines = [
        map_official_policy(line)
        for line in body_lines(official)
        if resource_url(line) not in personal_urls
        # 以个人哔哩哔哩规则替换上游宽泛媒体规则，避免影响其他媒体服务。
        and not resource_url(line).endswith("/StreamingSE.list")
    ]

    # 将宽泛与兜底规则放在最后，避免提前覆盖个人服务规则。
    broad_markers = ("/Streaming.list", "/Proxy.list", "/ASN.China.list")
    specific = [line for line in official_lines if not any(marker in line for marker in broad_markers)]
    broad = [line for line in official_lines if any(marker in line for marker in broad_markers)]

    lines = ["[filter_remote]"]
    if priority_direct:
        lines.extend(["", "# ======= 优先直连规则 ======= #"])
        lines.extend(priority_direct)
    if priority_ai:
        lines.extend(["", "# ======= AI平台优先规则（先于广告、隐私与宽泛分流） ======= #"])
        lines.extend(priority_ai)
    lines.extend(["", "# ======= 墨鱼官方规则（策略已映射到个人策略组） ======= #"])
    lines.extend(specific)
    lines.extend(["", "# ======= 个人规则（同 URL 时优先） ======= #"])
    lines.extend(personal_lines)
    lines.extend(["", "# ======= 墨鱼官方宽泛/兜底规则（放在最后） ======= #"])
    lines.extend(broad)
    return "\n".join(lines).rstrip() + "\n"


def local_rule_key(line: str) -> tuple[str, ...]:
    fields = tuple(field.strip().lower() for field in line.split(","))
    if not fields:
        return fields
    if fields[0] == "final":
        return ("final",)
    return fields[:2]


def merge_filter_local(official: str, personal: str) -> str:
    """按匹配目标合并本地规则，优先采用个人策略。"""
    personal_lines = body_lines(personal)
    personal_keys = {local_rule_key(line) for line in personal_lines}
    priority_ai = [line for line in personal_lines if line.endswith(",🤖 AI平台")]
    personal_lines = [line for line in personal_lines if line not in priority_ai]
    official_lines = [line for line in body_lines(official) if local_rule_key(line) not in personal_keys]
    lines = ["[filter_local]", "", "# ======= AI平台本地兜底（不依赖远程资源下载） ======= #"]
    lines.extend(priority_ai)
    lines.extend(["", "# ======= 墨鱼官方本地规则 ======= #"])
    lines.extend(official_lines)
    lines.extend(["", "# ======= 个人本地规则（重复目标时优先） ======= #"])
    lines.extend(personal_lines)
    return "\n".join(lines).rstrip() + "\n"


def enable_ipv6(dns_section: str) -> str:
    """沿用官方 DNS 配置，移除禁用 IPv6 的指令。"""
    lines = []
    for line in dns_section.splitlines():
        if line.strip().lower() == "no-ipv6":
            continue
        if "QuantumultX开启IPV6方法" in line:
            lines.append("# > 已按个人要求删除 no-ipv6；还需在 Quantumult X 的 VPN 设置中开启兼容性增强")
        else:
            lines.append(line)
    return "\n".join(lines).rstrip() + "\n"


def fetch_upstream() -> str:
    override = os.environ.get("OFFICIAL_CONFIG_FILE")
    if override:
        return Path(override).read_text(encoding="utf-8")
    result = subprocess.run(
        [
            "curl", "--fail", "--location", "--silent", "--show-error",
            "--retry", "5", "--retry-all-errors", "--retry-delay", "3",
            "--connect-timeout", "20", "--max-time", "120",
            "-A", "QuantumultX-PersonalConfig/1.0", UPSTREAM_URL,
        ],
        check=True,
        capture_output=True,
    )
    return result.stdout.decode("utf-8")


def fetch_private_server_tags(server_remote: str) -> list[str]:
    """提取订阅节点名称，供本地静态手动选择策略使用。"""
    source_url = next(
        (line.split(",", 1)[0].strip() for line in body_lines(server_remote)
         if line.startswith(("http://", "https://"))),
        None,
    )
    if not source_url:
        return []
    result = subprocess.run(
        ["curl", "--fail", "--location", "--silent", "--show-error",
         "--retry", "3", "--connect-timeout", "20", "--max-time", "120",
         source_url],
        check=True,
        capture_output=True,
    )
    tags = []
    seen = set()
    for line in result.stdout.decode("utf-8", errors="replace").splitlines():
        if "enabled=false" in line.lower():
            continue
        match = re.search(r"(?:^|,\s*)tag\s*=\s*([^,\r\n]+)", line)
        if match:
            tag = match.group(1).strip()
            if tag and tag not in seen:
                seen.add(tag)
                tags.append(tag)
    return tags


def expand_local_manual_policy(policy: str, server_remote: str) -> str:
    """将本地手动选择组展开为静态节点列表，保留暂时不可用的节点。"""
    tags = fetch_private_server_tags(server_remote)
    if not tags:
        return policy
    lines = []
    for line in policy.splitlines():
        if line.startswith("available=🛠️ 手动选择,"):
            lines.append("static=🛠️ 手动选择, " + ", ".join(tags))
        else:
            lines.append(line)
    return "\n".join(lines).rstrip() + "\n"


def build(personal_path: Path, output_path: Path, private_path: Path | None = None) -> None:
    upstream_prefix, upstream_sections = split_sections(fetch_upstream())
    _, personal_sections = split_sections(personal_path.read_text(encoding="utf-8"))
    personal_map = {name: body for name, body in personal_sections}
    private_map = {}
    if private_path:
        _, private_sections = split_sections(private_path.read_text(encoding="utf-8"))
        private_map = {name: body for name, body in private_sections}
    local_manual_policy = None
    if private_path and "server_remote" in private_map:
        local_manual_policy = expand_local_manual_policy(
            personal_map["policy"], private_map["server_remote"]
        )

    # 上游更新记录的装饰性英文标题统一显示为中文，保留作者署名。
    upstream_prefix = re.sub(
        r"(?m)^# 𝐂𝐮𝐭𝐭𝐥𝐞𝐟𝐢𝐬𝐡.*$",
        "# 墨鱼自用配置更新记录（作者：ddgksf2013）",
        upstream_prefix,
    )
    output = [upstream_prefix]
    for name, body in upstream_sections:
        if name == "server_remote":
            output.append(private_map.get(name, OFFICIAL_SERVER_REMOTE))
            continue
        if name == "dns":
            output.append(enable_ipv6(body))
            continue
        if name == "filter_remote":
            output.append(merge_filter_remote(body, personal_map[name]))
            continue
        if name == "filter_local":
            output.append(merge_filter_local(body, personal_map[name]))
            continue
        if name == "mitm" and name in private_map and meaningful(private_map[name]):
            output.append(private_map[name].rstrip() + "\n")
            continue
        if name in PERSONAL_OVERRIDE_SECTIONS and name in personal_map and meaningful(personal_map[name]):
            policy = local_manual_policy if name == "policy" and local_manual_policy else personal_map[name]
            output.append(policy.rstrip() + "\n")
        else:
            output.append(body)

    # 清理上游注释中的行尾空白，保证生成文件通过 Git 格式检查。
    merged = "\n".join(part.rstrip("\n") for part in output)
    output_path.write_text("\n".join(line.rstrip() for line in merged.splitlines()).rstrip() + "\n", encoding="utf-8")


def validate(path: Path, private_overlay: bool = False) -> None:
    text = path.read_text(encoding="utf-8")
    _, sections = split_sections(text)
    names = [name for name, _ in sections]
    if names.count("policy") != 1 or names.count("filter_remote") != 1 or names.count("filter_local") != 1:
        raise ValueError("生成配置必须各包含一个 policy、filter_remote 和 filter_local 分区")
    if names.count("server_remote") != 1:
        raise ValueError("生成配置必须包含一个 server_remote 分区")
    if private_overlay:
        if "p12 =" not in text or "passphrase =" not in text:
            raise ValueError("未合入私密 MITM 证书配置")
    else:
        if "Ruk1ng001/freeSub" not in text:
            raise ValueError("未合入官方临时节点订阅")
        if "gist.githubusercontent.com" in text:
            raise ValueError("个人订阅网址不能写入公开配置")
        if "p12 =" in text or "passphrase =" in text:
            raise ValueError("私密 MITM 证书配置不能公开发布")
    if re.search(r"(?m)^\s*no-ipv6\s*$", text):
        raise ValueError("生成配置必须保持 IPv6 启用")
    if "[rewrite_remote]" not in text or "BiliBiliAdsLite.conf" not in text:
        raise ValueError("未合入官方远程重写配置")
    if "🤖 AI平台" not in text:
        raise ValueError("未合入个人策略配置")
    if re.search(r"(?i)^(?:vmess|vless|trojan|ss|ssr|hysteria2?)://", text, re.MULTILINE):
        raise ValueError("节点连接网址不能提交到公开仓库")

    policies = set()
    for line in text.splitlines():
        match = re.match(r"^static=([^,]+)", line)
        if match:
            policies.add(match.group(1).strip())
        match = re.match(r"^url-latency-benchmark=([^,]+)", line)
        if match:
            policies.add(match.group(1).strip())
        match = re.match(r"^available=([^,]+)", line)
        if match:
            policies.add(match.group(1).strip())
    policies.update({"direct", "reject", "proxy"})

    missing = set()
    for line in text.splitlines():
        match = re.search(r"force-policy=([^,]+)", line)
        if match and match.group(1).strip() not in policies:
            missing.add(match.group(1).strip())
        match = re.match(r"^(?:host|host-suffix|host-keyword|ip-cidr|ip6-cidr|geoip|final),\s*(.+)$", line)
        if match:
            fields = [field.strip() for field in line.split(",")]
            target = fields[1] if fields[0] == "final" else fields[2]
            if target not in policies:
                missing.add(target)
    if missing:
        raise ValueError("规则引用了不存在的策略组：" + "、".join(sorted(missing)))


def main() -> None:
    if len(sys.argv) not in {3, 4}:
        raise SystemExit("用法：python3 脚本/构建圈X配置.py 配置/圈X分流模板.conf 配置/圈X自动配置.conf [圈X私密配置.conf]")
    output = Path(sys.argv[2])
    private_path = Path(sys.argv[3]) if len(sys.argv) == 4 else None
    build(Path(sys.argv[1]), output, private_path)
    validate(output, private_path is not None)


if __name__ == "__main__":
    main()
