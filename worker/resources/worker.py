import os
import sys
import asyncio
import logging
from typing import List
from nats.aio.client import Client as NATS
from google.protobuf.json_format import MessageToDict

from resources.task_handler import TaskHandlerFactory

# Add the parent directory of the project to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from proto.tasks_pb2 import Task, TaskResult, WorkerProperties


class Worker:
    """
    Worker node that connects to a NATS server, listens for tasks, and executes them
    """

    def __init__(
        self, worker_id: str, nats_server: str, capabilities: List[str]
    ) -> None:
        self.worker_id = worker_id
        self.capabilities = capabilities
        self.nats_server = nats_server
        self.nc = NATS()
        self.connected = False
        self.logger = logging.getLogger(__name__)

    async def connect(self) -> None:
        """
        Connects the worker to the NATS server
        """
        try:
            await self.nc.connect(
                servers=self.nats_server,
                max_reconnect_attempts=1,  # one attempt because we want to log reconnection
                disconnected_cb=self.disconnect,
            )
            self.connected = True
            logging.info(f"Worker {self.worker_id} connected to NATS")
        except Exception as e:
            logging.error(f"Worker {self.worker_id} failed to connect to NATS: {e}")
            self.connected = False

    async def disconnect(self) -> None:
        """
        Disconnects the worker from the NATS server
        """
        if self.connected:
            await self.nc.close()
            logging.info(f"Worker {self.worker_id} disconnected from NATS")
            self.connected = False

    async def listen_for_tasks(self) -> None:
        """
        Subscribes to the task topic and listens for incoming tasks
        """
        try:
            await self.nc.subscribe(
                f"worker.{self.worker_id}.task", cb=self.execute_task
            )
            logging.info(
                f"Worker {self.worker_id} subscribed to topic worker.{self.worker_id}.task"
            )
        except Exception as e:
            logging.error(f"Worker {self.worker_id} failed to subscribe to tasks: {e}")

    async def execute_task(self, msg) -> None:
        """
        Executes a task and publishes the result back to the controller
        """
        task = Task()
        task.ParseFromString(msg.data)
        task_type = MessageToDict(task)["type"]
        
        result = TaskResult(id=task.id, status="RUNNING")
        await self.nc.publish("worker.result", result.SerializeToString())
        self.logger.info(f"Received task {task.id}: {task.type}")

        if task_type not in self.capabilities:
            result.status = "FAILED"
            result.description = f"Task type: '{task_type}' not in capabilities: {', '.join(self.capabilities)}"
            await self.nc.publish("worker.result", result.SerializeToString())
            self.logger.warning(f"Task {task.id} failed: {result.description}")
            return

        try:
            # Emulate task execution
            async def execute_with_timeout() -> None:
                self.logger.debug(f"Executing task {task.id}")
                handler = TaskHandlerFactory.get_handler(task_type)
                result.result = handler.execute(task.operand1, task.operand2)

                result.status = "DONE"
                self.logger.info(f"Task {task.id} completed successfully")

            await asyncio.wait_for(execute_with_timeout(), timeout=task.timeout)

        except asyncio.TimeoutError:
            result.status = "FAILED"
            result.description = f"Task {task.id} timed out"
            self.logger.error(result.description)
        except Exception as e:
            result.status = "FAILED"
            result.description = str(e)
            self.logger.error(f"Task {task.id} failed with error: {e}", exc_info=e)

        await self.nc.publish("worker.result", result.SerializeToString())
        self.logger.debug(f"Task {task.id} result published: {result.status}")

    async def run(self) -> None:
        """
        Starts the worker:
        -connecting to the NATS server
        -listening for tasks
        """
        if not self.connected:
            await self.connect()

        if self.connected:
            await asyncio.gather(self.send_heartbeat(), self.listen_for_tasks())

    async def publish_capabilities(self) -> None:
        """
        Publishes the worker capabilities to the discovery topic
        """
        props = WorkerProperties(id=self.worker_id, capabilities=self.capabilities)
        await self.nc.publish("worker.discovery", props.SerializeToString())
        self.logger.debug(f"Published properties for worker {self.worker_id}")

    async def send_heartbeat(self) -> None:
        """
        Periodically sends a heartbeat with the worker capabilities to the discovery topic
        """
        while self.connected:
            try:
                await self.publish_capabilities()
                logging.info(f"Worker {self.worker_id} sent heartbeat/capabilities")
                await asyncio.sleep(10)
            except Exception as e:
                logging.error(f"Worker {self.worker_id} failed to send heartbeat: {e}")
                await self.disconnect()
