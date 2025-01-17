from abc import ABC, abstractmethod
from typing import Union, Type


class TaskHandler(ABC):
    """
    Abstract base class for arithmetic operation handlers
    Each handler validates the operands and performs a specific operation
    """
    @staticmethod
    def validate_operands(operand1: Union[int, float], operand2: Union[int, float]) -> None:
        """
        Validate that the operands are numeric

        Args:
            operand1 (Union[int, float]): The first operand
            operand2 (Union[int, float]): The second operand

        Raises:
            ValueError: If either operand is not a number
        """
        if not isinstance(operand1, (int, float)):
            raise ValueError(f"Invalid operand1: '{operand1}'. Must be numeric (int or float)")
        if not isinstance(operand2, (int, float)):
            raise ValueError(f"Invalid operand2: '{operand2}'. Must be numeric (int or float)")

    @staticmethod
    @abstractmethod
    def execute(operand1: Union[int, float], operand2: Union[int, float]) -> Union[int, float]:
        """
        Perform the arithmetic operation

        Args:
            operand1 (Union[int, float]): The first operand
            operand2 (Union[int, float]): The second operand

        Returns:
            Union[int, float]: The result of the operation
        """
        pass


# Concrete implementations
class AddHandler(TaskHandler):
    """
    Handler for addition operations
    """

    @staticmethod
    def execute(operand1: Union[int, float], operand2: Union[int, float]) -> Union[int, float]:
        TaskHandler.validate_operands(operand1, operand2)
        return operand1 + operand2


class SubtractHandler(TaskHandler):
    """
    Handler for subtraction operations
    """

    @staticmethod
    def execute(operand1: Union[int, float], operand2: Union[int, float]) -> Union[int, float]:
        TaskHandler.validate_operands(operand1, operand2)
        return operand1 - operand2


class MultiplyHandler(TaskHandler):
    """
    Handler for multiplication operations
    """

    @staticmethod
    def execute(operand1: Union[int, float], operand2: Union[int, float]) -> Union[int, float]:
        TaskHandler.validate_operands(operand1, operand2)
        return operand1 * operand2


class DivideHandler(TaskHandler):
    """
    Handler for division operations
    """

    @staticmethod
    def execute(operand1: Union[int, float], operand2: Union[int, float]) -> Union[int, float]:
        TaskHandler.validate_operands(operand1, operand2)
        if operand2 == 0:
            raise ValueError("Division by zero is not allowed")
        return operand1 / operand2


class TaskHandlerFactory:
    """
    Factory class for creating task handlers based on task type
    """
    handlers = {
        "ADD": AddHandler,
        "SUBTRACT": SubtractHandler,
        "MULTIPLY": MultiplyHandler,
        "DIVIDE": DivideHandler
    }

    @staticmethod
    def get_handler(task_type: str) -> Type[TaskHandler]:
        """
        Retrieve a handler class for the specified task type

        Args:
            task_type (str): Type of task (e.g., Add, Divide)

        Returns:
            Type[TaskHandler]: Class for the task type.

        Raises:
            ValueError: If no handler exists for the specified task type
        """
        if task_type not in TaskHandlerFactory.handlers:
            raise ValueError(f"No handler found for task type: '{task_type}'")
        return TaskHandlerFactory.handlers[task_type]
