# 个人分流规则使用说明

## 项目目录

```text
个人分流规则/
├── README.md                    # 完整中文使用说明，直接显示在 GitHub 首页
├── 圈X私密配置示例.conf
├── 配置/
│   ├── Clash主配置.yaml
│   ├── 圈X分流模板.conf
│   └── 圈X自动配置.conf
├── 规则集/
│   ├── Clash规则/               # AWS服务、Amazon电商、Wildberries电商、哔哩哔哩
│   └── 圈X规则/                 # 上述服务及苹果服务
├── 脚本/
│   ├── 构建圈X配置.py
│   └── 构建圈X本地配置.sh
└── .github/workflows/           # 内含检查上游规则.yml、更新圈X配置.yml
```

配置、规则和脚本统一使用中文目录。直接维护“配置”和“规则集”中的文件即可。GitHub 首页使用 `README.md`，客户端配置关键字、域名、上游网址、品牌名称与文件扩展名按原格式保留。

中文规则网址已进行百分号编码，确保客户端可以正常请求。重命名没有改变策略组、规则顺序或分流行为。

## 圈 X 自动配置

`配置/圈X自动配置.conf` 由 GitHub Actions 自动生成：以墨鱼官方配置为上游，采用官方通用设置、任务和重写；采用个人策略组；合并官方与个人分流并自动去重。

圈 X 订阅地址：

`https://raw.githubusercontent.com/Champion-Guan/personal-proxy-rules/main/%E9%85%8D%E7%BD%AE/%E5%9C%88X%E8%87%AA%E5%8A%A8%E9%85%8D%E7%BD%AE.conf`

Clash Party / SubStore 主配置地址：

`https://raw.githubusercontent.com/Champion-Guan/personal-proxy-rules/main/%E9%85%8D%E7%BD%AE/Clash%E4%B8%BB%E9%85%8D%E7%BD%AE.yaml`

官方配置每 6 小时检查一次。生成时会保留官方 DNS，但删除 `no-ipv6` 以允许 IPv6，并采用墨鱼官方的临时节点订阅。个人节点订阅地址不会写入本仓库。

### 本地私密合成

个人节点订阅和 MITM 证书不能与公开 GitHub 配置共存。将 `圈X私密配置示例.conf` 复制为 `圈X私密配置.conf` 并填写私密内容后，在本机运行：

```bash
bash 脚本/构建圈X本地配置.sh
```

这会直接更新当前用户圈 X iCloud Profiles 目录中的 `圈X本地配置.conf`，其中才包含个人节点订阅和 MITM。该文件不会进入 Git；圈 X 使用该本地文件时，配置更新需要在本机重新合成，公开 Raw 自动配置不含任何私密数据。脚本也兼容旧的 `quantumult-x.private.conf` 私密文件。需要继续写入旧输出文件或其他位置时，可通过环境变量 `QUANTUMULTX_OUTPUT_FILE` 指定完整输出路径。

私密配置中的 `YOUR_PASSPHRASE` 和 `YOUR_BASE64_P12` 为占位符，应替换为自己的证书内容；占位网址也应替换为自己的节点订阅。

## 自动化维护

GitHub Actions 的显示名称为“检查上游规则”和“更新圈X配置”，步骤说明和自动提交消息使用中文。原有定时计划与上游来源保持不变。第三方站点拒绝请求时，中文化本身不会修复其访问限制。

公开配置构建命令为：

```bash
python3 脚本/构建圈X配置.py 配置/圈X分流模板.conf 配置/圈X自动配置.conf
```

可通过 `OFFICIAL_CONFIG_FILE` 指定本机上游配置文件进行离线构建校验。

合并分流时，相同远程规则 URL 和相同本地匹配目标以个人配置为准。官方规则引用的策略会映射到现有个人策略组，宽泛的国际媒体、全球代理和国内规则放在个人服务规则之后，避免提前覆盖 Telegram、AI、YouTube、电商等个人分流。

这是一套从零设计的 Clash Party（Mihomo）和 Quantumult X 配置模板。

规则源采用分工模式：blackmatrix7 负责跨客户端的服务规则，Loyalsoldier 负责 Clash Party 的基础规则，MetaCubeX 负责 Mihomo 地理数据。

## 当前分类

### AI平台规则维护与手机更新

OpenAI / ChatGPT / Codex、Gemini、Claude / Claude Code 共用“🤖 AI平台”。核心规则统一维护在 `规则集/圈X规则/AI平台核心.list`，2026-10-21 按 MetaCubeX 的 OpenAI、Google Gemini、Anthropic 专项列表核对，并补充登录、验证、语音和静态资源依赖。该列表是本仓库维护的快照，不会因为请求间隔缩短就自动获得上游新增域名。

修改核心列表后，先运行 `python3 脚本/同步AI核心规则.py`，再运行 `python3 脚本/构建圈X配置.py 配置/圈X分流模板.conf 配置/圈X自动配置.conf`。同步脚本将同一份核心规则嵌入 Clash 主配置和圈 X 模板，远程规则下载失败时仍有本地兜底；GitHub Actions 会检查一致性和规则优先级。原有 blackmatrix7 远程补充列表保留，圈 X 的 AI 资源每 6 小时检查一次。

AI 核心规则优先于广告、隐私与国内分流。不把整个 `google.com`、`googleapis.com`、`cloudflare.com` 或 AWS 云服务强制归入 AI；但 Google 登录、Google 用户图片、验证等共享域名也会随“AI平台”选择出口。

手机圈 X 需要更新**完整配置**，然后更新分流资源并重连 VPN；只更新节点订阅不会更新本地规则。使用 iCloud 的 `圈X本地配置.conf` 时需同步更新该文件，不能只刷新 GitHub 上的公开配置。请在“AI平台”中选择服务支持地区且实际可用的节点；测速成功不代表能通过服务的地区或 IP 风控。若仍无法使用，检查圈 X 请求记录中的域名、命中策略和具体错误，不要仅凭无法打开就认定是规则问题。

- ✈️X电报：Telegram、X
- 🤖 AI平台：OpenAI、ChatGPT、Codex、Claude、Gemini
- ▶️YouTube
- 🎵Spotify
- 📺哔哩哔哩：🇹🇼 台湾节点、🇭🇰 香港节点或直连
- Apple 服务：直连
- 🛒Amazon电商，默认直连
- 🇷🇺Wildberries电商：覆盖 `wildberries.ru`、`wbbasket.ru` 及其子域名，默认直连；可切换节点选择、自动选择、手动选择、AWS、美国、日本、新加坡、香港、台湾。
- 🛡️ 广告拦截：`REJECT`，可切换为 `DIRECT` 关闭拦截
- 🛟 漏网之鱼：🚀 节点选择
- 节点：🇭🇰 香港、🇯🇵 日本、🇸🇬 新加坡、🇺🇸 美国、🇹🇼 台湾、☁️ AWS亚马逊服务器节点
- 国内域名和中国大陆 IP：通过 GeoSite/GeoIP 规则默认直连，不单独创建策略组。

## 规则源

- 服务规则：[blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)
- Clash Party 基础规则：[Loyalsoldier/clash-rules](https://github.com/Loyalsoldier/clash-rules)，通过 GitHub Actions 定期构建
- Mihomo 地理数据：[MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat)
- AWS 服务、Amazon 电商、Wildberries：本仓库自定义规则

## 使用前需要修改

主仓库地址：<https://github.com/Champion-Guan/personal-proxy-rules>

配置和自定义规则已经使用该仓库的 Raw 地址。

## 重要说明

- `配置/Clash主配置.yaml` 中的节点由 SubStore 合并你的机场订阅后提供。
- `配置/圈X分流模板.conf` 中的节点标签由 SubStore/圈X订阅提供；本文件负责策略组和远程分流。
- AWS亚马逊服务器节点是根据订阅节点名称筛选出来的节点组，名称中需要包含 `AWS`、`亚马逊` 或 `Amazon`。
- AWS 控制台和云服务域名使用“☁️ AWS亚马逊服务器节点”，不会被 Amazon 电商规则覆盖。
- Apple 服务（包括 `*.apple.com`、`*.icloud.com` 等）默认直连。
- Amazon电商规则只负责 Amazon 购物网站，默认直连。
- 地区测速依赖订阅节点名称包含地区关键词，例如“香港 / HK / Hong Kong”。如果机场使用完全不同的命名，需要调整正则表达式。
- blackmatrix7 和 Loyalsoldier 的远程规则更新周期设为 24 小时；规则源本身的实际发布时间由上游维护计划决定。
- Mihomo 的 `geosite.dat` 和 `geoip-lite.dat` 使用 MetaCubeX 最新发布地址。
