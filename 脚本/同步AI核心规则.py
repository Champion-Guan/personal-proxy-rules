#!/usr/bin/env python3
"""以圈 X 核心规则为唯一来源，同步两端本地兜底；--check 只校验。"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "规则集/圈X规则/AI平台核心.list"


def core_rules():
    rules = []
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        kind, domain, policy = line.split(",")
        if kind not in {"HOST", "HOST-SUFFIX"} or policy != "🤖 AI平台":
            raise ValueError(f"无效的 AI 核心规则：{line}")
        if not re.fullmatch(r"[a-z0-9.-]+", domain):
            raise ValueError(f"无效域名：{domain}")
        rules.append((kind, domain, policy))
    if len(rules) != len(set(rules)):
        raise ValueError("AI 核心规则存在重复项")
    return rules


def expected_files():
    rules = core_rules()
    clash = ROOT / "配置/Clash主配置.yaml"
    text = clash.read_text(encoding="utf-8")
    payload = "  ai_core:\n    type: inline\n    behavior: classical\n    format: yaml\n    payload:\n"
    payload += "".join(f"      - {kind.replace('HOST', 'DOMAIN')},{domain}\n" for kind, domain, _ in rules)
    text, count = re.subn(r"  (?:openai_core|ai_core):\n.*?(?=  lan:)", payload, text, flags=re.S)
    if count != 1:
        raise ValueError("找不到唯一的 Clash AI 核心规则块")
    text = text.replace("RULE-SET,openai_core,", "RULE-SET,ai_core,")
    yield clash, text

    qx = ROOT / "配置/圈X分流模板.conf"
    text = qx.read_text(encoding="utf-8")
    # 只替换旧 AI 本地规则；每次将完整核心规则放到本地分区最前。
    text = re.sub(r"(?m)^host(?:-suffix)?,[^\n]*,🤖 AI平台\n", "", text)
    text = text.replace("# AI核心规则开始\n", "").replace("# AI核心规则结束\n", "")
    block = "# AI核心规则开始\n" + "".join(f"{kind.lower()},{domain},{policy}\n" for kind, domain, policy in rules) + "# AI核心规则结束\n"
    text = text.replace("[filter_local]\n", "[filter_local]\n" + block)
    yield qx, text


def main():
    checking = "--check" in sys.argv
    for path, expected in expected_files():
        if checking:
            if path.read_text(encoding="utf-8") != expected:
                raise SystemExit(f"AI 核心规则尚未同步：{path.relative_to(ROOT)}")
        else:
            path.write_text(expected, encoding="utf-8")
    print(f"AI 核心规则{'一致性校验通过' if checking else '同步完成'}：{len(core_rules())} 条")


if __name__ == "__main__":
    main()
