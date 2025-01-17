import argparse
import re


def validate_nats_server(url: str) -> str:
    pattern = r"^nats://[a-zA-Z0-9_.-]+:[0-9]{1,5}$"
    if not re.match(pattern, url):
        raise argparse.ArgumentTypeError(
            "NATS server address must be in the format nats://<host>:<port>"
        )
    return url


def get_parser():
    parser = argparse.ArgumentParser(description="Start a Controller")
    parser.add_argument(
        "-n",
        "--nats-server",
        type=validate_nats_server,
        default="nats://127.0.0.2:4222",
        help="Address of the NATS server (default: nats://127.0.0.2:4222)",
    )
    return parser
