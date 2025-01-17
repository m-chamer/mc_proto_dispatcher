import pytest
from worker.resources.task_handler import (
    AddHandler,
    SubtractHandler,
    MultiplyHandler,
    DivideHandler,
    TaskHandlerFactory,
    TaskHandler,
)


@pytest.mark.parametrize("operand1, operand2, expected", [
    (1, 2, 3),
    (-1, -2, -3),
    (0.5, 1.5, 2.0),
])
def test_add_handler(operand1, operand2, expected):
    assert AddHandler.execute(operand1, operand2) == expected


@pytest.mark.parametrize("operand1, operand2, expected", [
    (5, 3, 2),
    (-1, -3, 2),
    (2.5, 1.5, 1.0),
])
def test_subtract_handler(operand1, operand2, expected):
    assert SubtractHandler.execute(operand1, operand2) == expected


@pytest.mark.parametrize("operand1, operand2, expected", [
    (5, 3, 15),
    (-1, -1, 1),
    (2.5, 2, 5.0),
])
def test_multiply_handler(operand1, operand2, expected):
    assert MultiplyHandler.execute(operand1, operand2) == expected


@pytest.mark.parametrize("operand1, operand2, expected", [
    (6, 3, 2),
    (-6, -3, 2),
    (7.5, 2.5, 3.0),
])
def test_divide_handler(operand1, operand2, expected):
    assert DivideHandler.execute(operand1, operand2) == expected


def test_divide_handler_zero_division():
    with pytest.raises(ValueError, match="Division by zero is not allowed"):
        DivideHandler.execute(5, 0)


@pytest.mark.parametrize("handler_type, handler_class", [
    ("ADD", AddHandler),
    ("SUBTRACT", SubtractHandler),
    ("MULTIPLY", MultiplyHandler),
    ("DIVIDE", DivideHandler),
])
def test_task_handler_factory(handler_type, handler_class):
    handler = TaskHandlerFactory.get_handler(handler_type)
    assert handler == handler_class


def test_task_handler_factory_invalid_type():
    with pytest.raises(ValueError, match="No handler found for task type: 'INVALID'"):
        TaskHandlerFactory.get_handler("INVALID")


@pytest.mark.parametrize("operand1, operand2", [
    ("a", 2),
    (2, "b"),
    ("x", "y"),
])
def test_validate_operands_invalid(operand1, operand2):
    with pytest.raises(ValueError, match="Invalid operand1|operand2"):
        AddHandler.execute(operand1, operand2)
