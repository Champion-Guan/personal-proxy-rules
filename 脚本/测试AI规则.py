#!/usr/bin/env python3
"""离线验证 AI 域名覆盖、优先级和跨客户端一致性。"""
from pathlib import Path
import runpy
import tempfile
import os
import unittest

ROOT = Path(__file__).resolve().parents[1]
SYNC = runpy.run_path(str(ROOT / "脚本/同步AI核心规则.py"))
BUILD = runpy.run_path(str(ROOT / "脚本/构建圈X配置.py"))


class AIRulesTests(unittest.TestCase):
    def test_generated_sources(self):
        for path, expected in SYNC["expected_files"]():
            self.assertEqual(path.read_text(encoding="utf-8"), expected)

    def test_service_domains(self):
        rules = SYNC["core_rules"]()
        for host in ["chatgpt.com", "auth.openai.com", "api.openai.com",
                     "ab.chatgpt.com", "ws.chatgpt.com", "cdn.oaistatic.com",
                     "files.oaiusercontent.com", "chatgpt.livekit.cloud",
                     "gemini.google.com", "generativelanguage.googleapis.com",
                     "robinfrontend-pa.googleapis.com", "accounts.google.com",
                     "geminiweb-pa.clients6.google.com", "oauth2.googleapis.com",
                     "claude.ai", "api.anthropic.com", "console.anthropic.com",
                     "platform.claude.com", "downloads.claude.ai",
                     "claudeusercontent.com", "challenges.cloudflare.com"]:
            self.assertTrue(any(host == domain or (kind == "HOST-SUFFIX" and host.endswith("." + domain))
                                for kind, domain, _ in rules), host)
        self.assertFalse(any(domain in {"google.com", "googleapis.com", "cloudflare.com", "amazonaws.com"}
                             for _, domain, _ in rules))

    def test_merge_priority(self):
        personal = "[filter_local]\nhost-suffix,chatgpt.com,🤖 AI平台\ngeoip,cn,direct\nfinal, 🛟 漏网之鱼\n"
        official = "[filter_local]\nhost-suffix,chatgpt.com,direct\nfinal,direct\n"
        merged = BUILD["merge_filter_local"](official, personal)
        self.assertNotIn("host-suffix,chatgpt.com,direct", merged)
        self.assertEqual(merged.count("final,"), 1)
        self.assertLess(merged.index("chatgpt.com"), merged.index("geoip,cn"))
        remote = BUILD["merge_filter_remote"](
            "[filter_remote]\nhttps://example.test/Proxy.list, force-policy=proxy\n",
            "[filter_remote]\nhttps://example.test/ads.list, force-policy=reject\nhttps://example.test/ai.list, force-policy=🤖 AI平台\n")
        self.assertLess(remote.index("/ai.list"), remote.index("/ads.list"))
        self.assertLess(remote.index("/ai.list"), remote.index("/Proxy.list"))

    def test_offline_build(self):
        previous = os.environ.get("OFFICIAL_CONFIG_FILE")
        os.environ["OFFICIAL_CONFIG_FILE"] = str(ROOT / "配置/圈X自动配置.conf")
        try:
            with tempfile.TemporaryDirectory(prefix="ai-rules-check-") as directory:
                output = Path(directory) / "圈X校验.conf"
                BUILD["build"](ROOT / "配置/圈X分流模板.conf", output)
                BUILD["validate"](output)
                text = output.read_text(encoding="utf-8")
                local = dict(BUILD["split_sections"](text)[1])["filter_local"]
                for kind, domain, policy in SYNC["core_rules"]():
                    self.assertIn(f"{kind.lower()},{domain},{policy}", local)
        finally:
            if previous is None:
                os.environ.pop("OFFICIAL_CONFIG_FILE", None)
            else:
                os.environ["OFFICIAL_CONFIG_FILE"] = previous


if __name__ == "__main__":
    unittest.main()
