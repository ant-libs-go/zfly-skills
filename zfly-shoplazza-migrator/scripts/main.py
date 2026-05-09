import sys
import os
import json
import argparse
import difflib
from transformer import detect_and_parse
from api_client import ShoplazzaClient


def load_config():
    config_path = os.path.join(os.getcwd(), ".env.json")
    if not os.path.exists(config_path):
        print("CONFIG_MISSING")
        sys.exit(1)
    with open(config_path, "r") as f:
        return json.load(f)


def read_data(path_or_str):
    if os.path.exists(path_or_str):
        with open(path_or_str, "r") as f:
            return f.read()
    return path_or_str


def main():
    parser = argparse.ArgumentParser(description="Shoplazza Manager CLI")
    subparsers = parser.add_subparsers(dest="command")

    parse_p = subparsers.add_parser("parse")
    parse_p.add_argument("--data", required=True)

    diff_p = subparsers.add_parser("diff-desc")
    diff_p.add_argument("--old", required=True)
    diff_p.add_argument("--new", required=True)

    create_p = subparsers.add_parser("create")
    create_p.add_argument("--data", required=True)
    create_p.add_argument("--desc", required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command in ("parse", "diff-desc"):
            pass
        else:
            config = load_config()
            client = ShoplazzaClient(config["spz_slug"], config["spz_access_token"])

        if args.command == "parse":
            content = read_data(args.data)
            payload = detect_and_parse(content)
            p = payload.product

            raw_dict = payload.to_dict()
            product_dict = raw_dict.get("product", {})

            out_dir = os.path.dirname(os.path.abspath(args.data))
            basic_path = os.path.join(out_dir, "product_basic.json")
            desc_path = os.path.join(out_dir, "product_description.json")

            desc = product_dict.pop("description", None) or ""
            with open(desc_path, "w") as f:
                f.write(desc)

            with open(basic_path, "w") as f:
                json.dump([raw_dict], f, indent=2, ensure_ascii=False)

            desc_text = (desc or "").strip()
            desc_status = f"{len(desc_text)} 字符" if desc_text else "无"
            opt_summary = ", ".join([f"{o.name}({len(o.values)})" for o in p.options])
            print(f"标题: {p.title}")
            print(f"描述: {desc_status}")
            print(f"选项: {opt_summary}")
            print(f"图片: {len(p.images)} 张")
            print(f"变体: {len(p.variants)} 个")
            print(f"FILE_PATH: {basic_path}")
            print(f"DESC_PATH: {desc_path}")
            print(f"DATA_DIR: {out_dir}")

        elif args.command == "diff-desc":
            with open(args.old) as f:
                old_lines = f.readlines()
            with open(args.new) as f:
                new_lines = f.readlines()
            diff = difflib.unified_diff(
                old_lines, new_lines, fromfile=args.old, tofile=args.new, lineterm=""
            )
            result = list(diff)
            if result:
                for line in result:
                    print(line)
            else:
                print("(无变化)")

        elif args.command == "create":
            with open(args.data) as f:
                products = json.load(f)
            with open(args.desc) as f:
                description = f.read()

            for i, item in enumerate(products):
                payload = item if "product" in item else {"product": item}
                if description.strip():
                    payload["product"]["description"] = description

                res = client.create_product(payload)
                if res:
                    p = res.get("data", {}).get("product", {})
                    print(
                        f"[操作类型: 创建] - [状态: 成功] - [{p.get('title')}] - [ID: {p.get('id')}] - [链接: https://{config['spz_slug']}.myshoplaza.com/products/{p.get('handle')}]"
                    )
                else:
                    print(f"[操作类型: 创建] - [状态: 失败] - [SPU {i+1}]")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
