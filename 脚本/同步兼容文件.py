#!/usr/bin/env python3
"""维护旧规则网址的兼容副本，防止尚未更新的客户端订阅失效。"""

from pathlib import Path
import sys


项目目录 = Path(__file__).resolve().parent.parent
兼容映射 = {
    "mihomo.yaml": "配置/Clash主配置.yaml",
    "quantumult-x.conf": "配置/圈X分流模板.conf",
    "quantum-x-auto.conf": "配置/圈X自动配置.conf",
    "rules/mihomo/aws-services.yaml": "规则集/Clash规则/AWS服务.yaml",
    "rules/mihomo/amazon-shopping.yaml": "规则集/Clash规则/Amazon电商.yaml",
    "rules/mihomo/wildberries.yaml": "规则集/Clash规则/Wildberries电商.yaml",
    "rules/mihomo/bilibili.yaml": "规则集/Clash规则/哔哩哔哩.yaml",
    "rules/quantumult-x/aws-services.list": "规则集/圈X规则/AWS服务.list",
    "rules/quantumult-x/amazon-shopping.list": "规则集/圈X规则/Amazon电商.list",
    "rules/quantumult-x/wildberries.list": "规则集/圈X规则/Wildberries电商.list",
    "rules/quantumult-x/bilibili.list": "规则集/圈X规则/哔哩哔哩.list",
    "rules/quantumult-x/apple-services.list": "规则集/圈X规则/苹果服务.list",
}


def main() -> None:
    if sys.argv[1:] not in ([], ["--check"]):
        raise SystemExit("用法：python3 脚本/同步兼容文件.py [--check]")
    仅检查 = sys.argv[1:] == ["--check"]
    不一致 = []
    for 旧路径, 中文路径 in 兼容映射.items():
        目标 = 项目目录 / 旧路径
        内容 = (项目目录 / 中文路径).read_bytes()
        if 仅检查:
            if not 目标.is_file() or 目标.read_bytes() != 内容:
                不一致.append(旧路径)
        else:
            目标.parent.mkdir(parents=True, exist_ok=True)
            目标.write_bytes(内容)
    if 不一致:
        raise SystemExit("兼容文件未同步：" + "、".join(不一致))
    print("兼容文件校验通过" if 仅检查 else "旧网址兼容文件已同步")


if __name__ == "__main__":
    main()
