import argparse


def main():
    parser = argparse.ArgumentParser(
        description="ChemMind Learn —— 自我进化AI学习平台"
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["cli", "web"],
        default="cli",
        help="运行模式: cli (命令行) 或 web (网页)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=None,
        help="Web服务端口 (默认8000)",
    )

    args = parser.parse_args()

    if args.mode == "web":
        from ui.web import main as web_main
        if args.port:
            from config import config
            config.WEB_PORT = args.port
        port = config.WEB_PORT
        print(f"[ChemMind] Web server starting: http://localhost:{port}")
        web_main()
    else:
        from ui.cli import main as cli_main
        cli_main()


if __name__ == "__main__":
    main()