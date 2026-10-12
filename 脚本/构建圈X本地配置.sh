#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
private_overlay="$repo_dir/圈X私密配置.conf"
output="${QUANTUMULTX_OUTPUT_FILE:-$HOME/Library/Mobile Documents/iCloud~com~crossutility~quantumult-x/Documents/Profiles/圈X本地配置.conf}"

# 兼容中文化之前已经在本机配置好的私密文件。
if [[ ! -f "$private_overlay" && -f "$repo_dir/quantumult-x.private.conf" ]]; then
  private_overlay="$repo_dir/quantumult-x.private.conf"
fi

if [[ ! -f "$private_overlay" ]]; then
  echo "缺少私密配置文件：$private_overlay" >&2
  exit 1
fi

mkdir -p "$(dirname "$output")"

python3 "$repo_dir/脚本/构建圈X配置.py" \
  "$repo_dir/配置/圈X分流模板.conf" \
  "$output" \
  "$private_overlay"

echo "已生成本地配置：$output"
