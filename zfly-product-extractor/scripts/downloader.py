import os
import subprocess
import sys
import re
from urllib.parse import urlparse, unquote


def run_jq(json_path: str, jq_expr: str) -> list[str]:
    result = subprocess.run(
        ["jq", "-r", jq_expr, json_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: jq 解析失败: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        print("ERROR: jq 未提取到任何图片 URL", file=sys.stderr)
        sys.exit(1)
    return lines


def normalize_url(raw_url: str) -> str:
    url = raw_url.strip()
    if url.startswith("//"):
        url = "https:" + url
    query_start = url.find("?")
    if query_start != -1:
        url = url[:query_start]
    return url


def extract_extension(url: str) -> str:
    path = urlparse(url).path
    path = unquote(path)
    match = re.search(r"\.([a-zA-Z0-9]+)$", path)
    if match:
        return match.group(1).lower()
    return "jpg"


def download_images(urls: list[str], output_dir: str) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    downloaded = []
    for idx, raw_url in enumerate(urls, start=1):
        url = normalize_url(raw_url)
        ext = extract_extension(url)
        filename = f"{idx:03d}.{ext}"
        filepath = os.path.join(output_dir, filename)
        result = subprocess.run(
            ["curl", "-L", "-s", "-o", filepath, url],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"WARNING: 下载失败 {url}: {result.stderr.strip()}", file=sys.stderr)
        else:
            downloaded.append(filename)
    return downloaded
