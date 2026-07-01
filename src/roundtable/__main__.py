"""CLI 入口 —— python -m roundtable"""

import argparse
import asyncio
import sys

from . import run_roundtable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Roundtable —— 简单多角色圆桌讨论",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python -m roundtable --code 600519 --rounds 3
    python -m roundtable -c 000001 -r 2 --roles-dir config/roles -o ./reports
        """,
    )
    parser.add_argument(
        "-c", "--code",
        required=True,
        help="股票代码（如 600519）",
    )
    parser.add_argument(
        "-r", "--rounds",
        type=int,
        default=1,
        help="交流轮次（默认 1，范围 1-10）",
    )
    parser.add_argument(
        "--roles-dir",
        type=str,
        default="config/roles",
        help="角色配置文件夹路径（默认 config/roles）",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default=".",
        help="Markdown 报告输出目录（默认当前目录）",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default="sonnet",
        choices=["sonnet", "opus", "haiku"],
        help="Claude 模型（默认 sonnet）",
    )
    args = parser.parse_args()

    if args.rounds < 1 or args.rounds > 10:
        parser.error("轮次必须在 1 到 10 之间")

    return args


def main() -> None:
    args = parse_args()
    try:
        md_path = asyncio.run(
            run_roundtable(
                code=args.code,
                rounds=args.rounds,
                roles_dir=args.roles_dir,
                output_dir=args.output_dir,
                model=args.model,
            )
        )
        print(f"\n 报告已生成: {md_path.absolute()}")
    except RuntimeError as e:
        print(f"\n[错误] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[运行出错] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
