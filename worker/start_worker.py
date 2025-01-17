import asyncio
import logging
import uuid
from resources.argument_parser import get_parser
from resources.worker import Worker


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
    Main entry point for the worker
    Parses arguments, initializes the worker, and handles the worker job
    """
    parser = get_parser()
    args = parser.parse_args()

    # Ensure worker id is unique
    full_worker_id = f"{args.worker_id}-{uuid.uuid4()}"

    configure_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Starting worker with ID: {full_worker_id}")
    logger.info(f"NATS Server: {args.nats_server}")
    logger.info(f"Capabilities: {', '.join(args.capabilities)}")

    worker = Worker(
        worker_id=full_worker_id,
        nats_server=args.nats_server,
        capabilities=args.capabilities
    )

    while True:
        try:
            await worker.run()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        finally:
            await worker.disconnect()
            logging.info(f"Reconnecting {full_worker_id} after a delay...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Worker shutdown initiated by user.")