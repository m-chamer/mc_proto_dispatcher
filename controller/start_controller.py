import asyncio
import logging
from resources.argument_parser import get_parser
from resources.controller import (
    Controller,
    NATSClientImpl,
    WorkerManagerImpl,
    TaskManagerImpl,
)


def configure_logging():
    """
    Configure logging for the worker
    Sets logging level, format, and suppresses noisy nats logs
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.getLogger("nats.aio.client").setLevel(logging.CRITICAL)


async def main() -> None:
    """
    Main entry point for the controller
    Parses arguments, initializes the controller
    """
    parser = get_parser()
    args = parser.parse_args()

    configure_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Controller")
    logger.info(f"NATS Server: {args.nats_server}")

    nats_client = NATSClientImpl(args.nats_server)
    worker_manager = WorkerManagerImpl()
    task_manager = TaskManagerImpl()

    controller = Controller(nats_client, worker_manager, task_manager)
    await controller.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Worker shutdown initiated by user.")
