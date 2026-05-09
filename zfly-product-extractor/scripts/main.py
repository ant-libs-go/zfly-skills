import sys
import os
import argparse
from downloader import run_jq, download_images


def main():
    parser = argparse.ArgumentParser(description="Product Extractor CLI")
    subparsers = parser.add_subparsers(dest="command")

    download_p = subparsers.add_parser("download-images", help="从商品 JSON 中提取图片 URL 并下载")
    download_p.add_argument("--data", required=True, help="product.json 的路径")
    download_p.add_argument("--jq-path", required=True, help="jq 表达式，用于提取图片 URL，例如 '.product.images[].src'")
    download_p.add_argument("--output-dir", required=True, help="图片下载目录")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "download-images":
            if not os.path.exists(args.data):
                print(f"ERROR: 文件不存在 {args.data}", file=sys.stderr)
                sys.exit(1)

            urls = run_jq(args.data, args.jq_path)
            downloaded = download_images(urls, args.output_dir)

            for f in downloaded:
                print(f)
            print(f"\n共下载 {len(downloaded)}/{len(urls)} 张图片到 {args.output_dir}")

    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
