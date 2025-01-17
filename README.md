# mc_proto_dispatcher

`mc_proto_dispatcher` is a Python-based task distribution system designed to handle arithmetic operations and distribut to worker nodes. This project demonstrates key principles of distributed systems, use **NATS** for communication and **Protobuf** for message serialization.

## Features
- **Task Distribution**: Distributes arithmetic tasks (`Add`, `Subtract`, `Multiply`, `Divide`) from a controller node to worker nodes.
- **Worker Capabilities**: Workers broadcast their capabilities dynamically (e.g. `Add`, `Subtract`).
- **Health Checks**: Monitors worker nodes are available and functional by sending Heartbeat messages that include their capabilities.
- **Task Status Tracking**: Tracks task statuses in the controller node:
  - `RUNNING`, `DONE`, `FAILED`
  - **TBD**: Implement task queuing and status `QUEUED`.
- **Timeout Handling**: Automatically marks tasks as `FAILED` if they exceed a specified timeout.
  - **TBD**: Emulate task processing time for test purposes.
- **Dynamic Discovery**: Worker nodes dynamically publish their capabilities to the controller for real-time updates.
- **Protocol Buffers**: Provides structured way to communicate between nodes.
- **Planned Features**:
  - Interactive task submission interface (currently mocked, sending test tasks during worker discovery).


## Architecture

The system consists of:

1. **Controller Node**:
   - Manages task distribution to worker nodes.
   - Tracks task statuses in-memory.
   - Ensures tasks are assigned to appropriate worker based on their capabilities.

2. **Worker Nodes**:
   - Perform arithmetic tasks (`Add`, `Subtract`, `Multiply`, `Divide`).
   - Publish capabilities to the controller.
   - Reconnect automatically if the connection to the controller is lost.

3. **NATS Messaging**:
   - Passing message between controller and workers.

## Requirements

- Python 3.9+
- NATS server
- Protobuf

## Setup and Installation

### 1. Clone the Repository
```bash
git clone https://github.com/m-chamer/mc_proto_dispatcher.git
cd mc_proto_dispatcher
```

### 2. Install Dependencies
Create a virtual environment and install the required packages:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Start the NATS Server
Ensure a NATS server is running. You can download and run NATS from [nats.io](https://nats.io/download/):
```bash
nats-server -a 127.0.0.2
```

### 4. Run the Controller
Start the controller:
```bash
python controller/start_controller.py
```

### 5. Run Worker Nodes
Start worker nodes in separate terminals:
```bash
python worker/start_worker.py -w Worker1 -c Add Divide
```

## Usage

### Task Submission
**TBD:** for now feature is mocked, send hardcoded task on worker discovery
- **task_id**: Unique ID of the task.
- **task_type**: One of `Add`, `Subtract`, `Multiply`, `Divide`.
- **operand1**: First operand for the task.
- **operand2**: Second operand for the task.
- **timeout**: Maximum time to complete the task (default: 10 seconds).
- **processing_time**: Emulated task processing time in seconds.

Example hardcoded method for a task submission:
```python
await self.submit_task(
            task_id="1",
            task_type="DIVIDE",
            operand1=1,
            operand2=10,
            timeout=5,
            processing_time=1,
        )
```

### Monitoring Task Status
Task statuses (`QUEUED`, `RUNNING`, `DONE`, `FAILED`) are logged to the console.

### Health Check
The system periodically checks the availability of worker nodes. If a worker becomes unresponsive, it is removed from available workers nodes.

## Development

### Protobuf Compilation
Generate Python classes from the `.proto` files:
```bash
protoc --python_out=. --proto_path=proto_files proto_files/*.proto
```

### Testing
Run unit tests:
```bash
pytest
```

## Design Principles

- **OOP Design**: Implements clean, object-oriented principles.
- **In-Memory Storage**: Simplifies task tracking without a DBMS.
- **Decoupled Architecture**: Utilizes NATS for loose coupling between nodes.
- **Timeouts**: Ensures tasks don’t hang indefinitely.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
