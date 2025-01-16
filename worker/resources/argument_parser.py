import argparse
import re

VALID_CAPABILITIES = {"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE"}


def validate_capabilities(value: str) -> str:
    normalized_value = value.upper()
    if normalized_value not in VALID_CAPABILITIES:
        raise argparse.ArgumentTypeError(
            f"Invalid capabilities: {value} "
            f"Valid options are: {', '.join(VALID_CAPABILITIES)}"
        )
    return normalized_value


def validate_worker_id(worker_id: str) -> str:
    if not worker_id or not worker_id.isalnum():
        raise argparse.ArgumentTypeError(
            "Worker ID must be a non-empty alphanumeric str"
        )
    return worker_id


def validate_nats_server(url: str) -> str:
    pattern = r"^nats://[a-zA-Z0-9_.-]+:[0-9]{1,5}$"
    if not re.match(pattern, url):
        raise argparse.ArgumentTypeError(
            "NATS server address must be in the format nats://<host>:<port>"
        )
    return url


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start a Worker")

    parser.add_argument(
        "-w",
        "--worker-id",
        type=validate_worker_id,
        required=True,
        help="Base identifier for the worker. A unique UUID will be appended to this ID",
    )

    parser.add_argument(
        "-n",
        "--nats-server",
        type=validate_nats_server,
        default="nats://127.0.0.2:4222",
        help="Address of the NATS server (default: nats://127.0.0.2:4222)",
    )

    parser.add_argument(
        "-c",
        "--capabilities",
        type=validate_capabilities,
        nargs="*",
        default=[],
        help=(
            f"Optional: Space-separated list of capabilities supported by the worker "
            f"Valid options (case-insensitive): {', '.join(VALID_CAPABILITIES)}"
        ),
    )

    return parser
