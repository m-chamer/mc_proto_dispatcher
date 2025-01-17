import os
import sys
import time
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Union, Optional, Callable

from nats.aio.client import Client as NATS
from google.protobuf.json_format import MessageToDict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from proto.tasks_pb2 import Task, TaskResult, WorkerProperties, TaskType


# Interfaces and Abstract Classes

class NATSClient(ABC):
    """
    Interface for a messaging client
    """
    @abstractmethod
    async def connect(self) -> None:
        """
        Establish a connection to the messaging system
        """
        pass

    @abstractmethod
    async def publish(self, subject: str, message: bytes) -> None:
        """
        Publish a message to the subject
        Args:
            subject (str): Subject to publish
            message (bytes): Message payload
        """
        pass

    @abstractmethod
    async def subscribe(self, subject: str, callback: Callable) -> None:
        """
        Subscribe to a specific subject with a callback
        Args:
            subject (str): Subject to subscribe
            callback (Callable): Callback function to handle received messages
        """
        pass

    @abstractmethod
    async def monitor_disconnection(self) -> None:
        """
        Monitor the connection and handle disconnections
        """
        pass


class WorkerManager(ABC):
    """
   Interface for managing worker registration, removal, and task assignment
   """
    @abstractmethod
    def register_worker(self, worker_id: str, capabilities: List[str]) -> None:
        """
        Register a new worker with capabilities
        Args:
            worker_id (str): Unique ID of the worker
            capabilities (List[str]): List of task types the worker can handle
        """
        pass

    @abstractmethod
    async def remove_inactive_workers(self) -> None:
        """
        Remove workers that have not sent a heartbeat within a specified interval
        """
        pass

    @abstractmethod
    def get_suitable_worker(self, task_type: str) -> Optional[str]:
        """
        Find a suitable worker for a given task type
        Args:
            task_type (str): Type of task that a worker should do
        Returns:
            Optional[str]: The ID of a suitable worker, or None if not suitable worker
        """
        pass


class TaskManager(ABC):
    """
    Interface for managing tasks, including adding, updating, and getting
    """
    @abstractmethod
    def add_task(self, task_id: str, task: Dict) -> None:
        """
        Add a new task to the system
        Args:
            task_id (str): The unique ID of the task
            task (Dict): The task details
        """
        pass

    @abstractmethod
    def update_task(self, task_id: str, status: str) -> None:
        """
        Update the status of an existing task
        Args:
            task_id (str): The unique ID of the task
            status (str): The new status of the task
        """
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Dict:
        """
        Retrieve details of a specific task
        Args:
            task_id (str): The unique ID of the task
        Returns:
            Dict: The task details
        """
        pass


# Concrete Implementations
class NATSClientImpl(NATSClient):
    """
    Implementation of the MessagingClient interface using NATS
    """
    def __init__(self, nats_server: str) -> None:
        """
        Initialize the NATS client
        Args:
            nats_server (str): The address of the NATS server
        """
        self.nats_server = nats_server
        self.nc = NATS()
        self.disconnected_event = asyncio.Event()
        self.logger = logging.getLogger(__name__)

    async def connect(self) -> None:
        """
        Establish a connection to the NATS server
        """
        while True:
            try:
                await self.nc.connect(
                    servers=self.nats_server,
                    disconnected_cb=self.on_disconnection,
                    max_reconnect_attempts=1,
                )
                self.logger.info("Successfully connected to NATS server")
                break
            except Exception as e:
                self.logger.error(
                    f"Failed to connect to NATS server: {e}. Retrying in 5 seconds..."
                )
                await asyncio.sleep(5)

    async def publish(self, subject: str, message: bytes) -> None:
        """
        Publish a message to the subject
        Args:
            subject (str): Subject to publish
            message (bytes): Message payload
        """
        await self.nc.publish(subject, message)

    async def subscribe(self, subject: str, callback: Callable) -> None:
        """
        Subscribe to a specific subject with a callback.
        Args:
            subject (str): Subject to subscribe
            callback (Callable): Callback function to handle received messages
        """
        await self.nc.subscribe(subject, cb=callback)

    async def on_disconnection(self):
        """
        Action on disconnection from the NATS server
        """
        self.disconnected_event.set()
        self.logger.warning("Disconnected from NATS server")

    async def monitor_disconnection(self):
        """
        Wait for a disconnection event and raise error
        """
        await self.disconnected_event.wait()
        raise ConnectionError("Lost connection to NATS server")


class WorkerManagerImpl(WorkerManager):
    """
    Manages worker registration and task assignment
    """
    def __init__(self) -> None:
        """
        Initialize the worker manager
        """
        self.workers: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)

    def register_worker(self, worker_id: str, capabilities: List[str]) -> None:
        """
        Register a new worker or update the heartbeat for existing worker
        Args:
            worker_id (str): Unique ID of the worker
            capabilities (List[str]): List of task types the worker can handle
        """
        if worker_id in self.workers:
            self.workers[worker_id]["last_heartbeat"] = time.time()
            return
        self.workers[worker_id] = {
            "capabilities": capabilities,
            "last_heartbeat": time.time(),
        }
        self.logger.info(f"Registered new worker: {worker_id}")

    async def remove_inactive_workers(self) -> None:
        """
        Remove workers that have not sent a heartbeat within 15s
        """
        while True:
            current_time = time.time()
            inactive_workers = [
                worker_id
                for worker_id, props in self.workers.items()
                if current_time - props["last_heartbeat"] > 15
            ]
            for worker_id in inactive_workers:
                del self.workers[worker_id]
                self.logger.info(f"Remove inactive worker: {worker_id}")
            await asyncio.sleep(5)

    def get_suitable_worker(self, task_type: str) -> Optional[str]:
        """
        Find a suitable worker for a given task type
        Args:
            task_type (str): Type of task that a worker should do
        Returns:
            Optional[str]: The ID of a suitable worker, or None if not suitable worker
        """
        self.logger.info(f"Looking for suitable worker for task: {task_type}")
        for worker_id, props in self.workers.items():
            if task_type in props.get("capabilities", []):
                self.logger.info(f"Suitable worker found: {worker_id}")
                return worker_id
        self.logger.warning("Not found suitable worker")
        return None


class TaskManagerImpl(TaskManager):
    """
    Manages tasks, including their states and data
    TODO: add task queue handling
    """
    def __init__(self) -> None:
        """
        Initialize the task manager
        """
        self.tasks: Dict[str, Dict] = {}

    def add_task(self, task_id: str, task: Dict) -> None:
        """
        Add a new task to the system
        Args:
            task_id (str): The unique ID of the task
            task (Dict): The task details
        """
        self.tasks[task_id] = task

    def update_task(self, task_id: str, status: str) -> None:
        """
                Update the status of an existing task
                Args:
                    task_id (str): The unique ID of the task
                    status (str): The new status of the task
                """
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = status

    def get_task(self, task_id: str) -> Dict:
        """
        Retrieve details of a specific task
        Args:
            task_id (str): The unique ID of the task
        Returns:
            Dict: The task details
        """
        return self.tasks.get(task_id, {})


# Controller
class Controller:
    """
    Orchestrates task distribution and worker communication.
    """
    def __init__(
        self,
        nats_client: NATSClient,
        worker_manager: WorkerManager,
        task_manager: TaskManager,
    ) -> None:
        """
        Initialize the controller.

        Args:
            nats_client (MessagingClient): Messaging client for communication
            worker_manager (WorkerManager): Manager for worker operations
            task_manager (TaskManager): Manager for task operations
        """
        self.nats_client = nats_client
        self.worker_manager = worker_manager
        self.task_manager = task_manager
        self.logger = logging.getLogger(__name__)

    async def register_worker(self, msg) -> None:
        """
        Handle worker registration messages.

        Args:
            msg: The message containing worker properties.
        """
        worker_properties = WorkerProperties()
        worker_properties.ParseFromString(msg.data)
        worker_properties_dict = MessageToDict(worker_properties)

        self.worker_manager.register_worker(
            worker_properties.id, worker_properties_dict["capabilities"]
        )
        # Dirty hack to check if basic functionality works
        # since CLI is not ready
        # on discover worker submit a test task
        await self.submit_task(
            task_id="1",
            task_type="DIVIDE",
            operand1=1,
            operand2=10,
            timeout=5,
            processing_time=1,
        )

    async def process_result(self, msg) -> None:
        """
        Handle task result messages

        Args:
            msg: The message containing task results
        """
        result = TaskResult()
        result.ParseFromString(msg.data)
        result_dict = MessageToDict(result)
        self.logger.info(
            f"Result for task: {result.id} received, "
            f"status: {result_dict['status']}, "
            f"description: {result.description}, "
            f"result: {result.result}"
        )

    async def submit_task(
        self,
        task_id: str,
        task_type: str,
        operand1: Union[int, float],
        operand2: Union[int, float],
        timeout: int,
        processing_time: int,
    ) -> None:
        """
        Submit a new task to a proper worker

        Args:
            task_id (str): Unique ID of the task
            task_type (str): Type of task
            operand1 (Union[int, float]): First operand for the task
            operand2 (Union[int, float]): Second operand for the task
            timeout (int): Timeout for task execution in seconds
            processing_time (int): Emulated task processing time in seconds
        """
        worker_id = self.worker_manager.get_suitable_worker(task_type)
        task = Task(
            id=task_id,
            type=task_type,
            operand1=float(operand1),
            operand2=float(operand2),
            timeout=timeout,
            processing_time=processing_time,
        )
        self.logger.debug(f"submit task worker_id")
        self.logger.debug(f"{task.type}")
        self.logger.debug(f"{TaskType.ADD}")
        self.logger.debug(f"{task}")

        if worker_id:
            self.logger.debug(f"submit task worker_id inside if")
            await self.nats_client.publish(
                f"worker.{worker_id}.task", task.SerializeToString()
            )
            self.logger.info(f"Task {task.id} sent to worker {worker_id}")

    async def monitor_disconnection(self) -> None:
        """
        Wait for a disconnection event and raise error
        """
        await self.nats_client.monitor_disconnection()

    async def run(self) -> None:
        """
        Run the controller to manage task distribution and worker communication
        """
        await self.nats_client.connect()
        await self.nats_client.subscribe("worker.discovery", self.register_worker)
        await self.nats_client.subscribe("worker.result", self.process_result)

        try:
            await asyncio.gather(
                self.worker_manager.remove_inactive_workers(),
                self.monitor_disconnection(),
            )
        except ConnectionError as e:
            self.logger.error(e)
