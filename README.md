# Engineering Team — CrewAI Multi-Agent Software Engineering Crew

A CrewAI-based multi-agent software engineering workflow that takes high-level software requirements and coordinates a team of specialized AI engineering agents to design, implement, build a frontend, and test a Python application.

## Overview

This project demonstrates how multiple specialized CrewAI agents can collaborate on a real software-engineering task.

The current example asks the crew to build a simple **account management system for a trading simulation platform**.

The system is required to support:

* Creating an account
* Depositing funds
* Withdrawing funds
* Buying shares
* Selling shares
* Calculating total portfolio value
* Calculating profit/loss from the initial deposit
* Reporting holdings at a point in time
* Reporting profit/loss at a point in time
* Listing historical transactions
* Preventing withdrawals that would result in a negative balance
* Preventing purchases when the user cannot afford the shares
* Preventing users from selling shares they do not own

The application also has access to a `get_share_price(symbol)` function with fixed test prices for AAPL, TSLA, and GOOGL.

---

## Architecture

The project uses four specialized CrewAI agents working in a sequential workflow:

```text
                    ┌─────────────────────────┐
                    │   Engineering Lead      │
                    │                         │
                    │ Requirements → Design   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    Backend Engineer     │
                    │                         │
                    │ Design → Python Code    │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Frontend Engineer     │
                    │                         │
                    │ Backend → Gradio UI     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     Test Engineer       │
                    │                         │
                    │ Code → Unit Tests       │
                    └─────────────────────────┘
```

The CrewAI process is configured as **sequential**, allowing the output/context of earlier tasks to be used by subsequent agents.

---

## Agents

### 1. Engineering Lead

The Engineering Lead is responsible for converting high-level requirements into a detailed technical design.

Responsibilities:

* Analyze the requirements
* Design the system
* Identify modules, classes, and functions
* Define function/method signatures
* Assign work to the backend, frontend, and test engineers
* Use Context7 MCP to verify relevant APIs
* Provide Gradio 6 API guidance to the frontend engineer

The agent is configured to use:

```text
openai/gpt-5.4-mini
```

### 2. Backend Engineer

The Backend Engineer implements the system designed by the Engineering Lead.

Responsibilities:

* Implement the backend Python code
* Follow the design produced by the Engineering Lead
* Use the Python standard library
* Write and execute code through the sandbox
* Avoid frontend/UI implementation

### 3. Frontend Engineer

The Frontend Engineer creates the user interface using Gradio.

Responsibilities:

* Build a professional Gradio UI
* Demonstrate the backend functionality
* Create `app.py`
* Validate that the Gradio application can be constructed
* Create `_validate.py`
* Ensure the UI works in light and dark modes
* Use the specified visual palette

### 4. Test Engineer

The Test Engineer validates the backend implementation.

Responsibilities:

* Write unit tests
* Use Python's built-in `unittest`
* Execute the tests
* Identify and fix backend defects
* Continue until the tests pass
* Avoid breaking the Gradio frontend
* Generate a test result summary

---

## Workflow

The crew contains four main tasks.

### 1. Design Task

The Engineering Lead receives the requirements and creates a detailed technical design.

Output:

```text
sandbox/design.md
```

The design includes:

* Modules
* Classes
* Functions
* Function signatures
* Responsibilities
* Work assignment between engineers

The Engineering Lead does **not** implement the code.

---

### 2. Code Task

The Backend Engineer receives the design and requirements and implements the backend.

The backend code is written inside the sandbox.

---

### 3. Frontend Task

The Frontend Engineer creates a Gradio application around the backend.

The main frontend file is:

```text
sandbox/app.py
```

A validation script is also created:

```text
sandbox/_validate.py
```

The validation script verifies that the Gradio application can be constructed successfully without calling `.launch()`.

---

### 4. Test Task

The Test Engineer creates unit tests for the backend.

The tests are stored in:

```text
sandbox/test_account_model.py
```

The task also produces:

```text
sandbox/test_summary.md
```

The test engineer uses Python's built-in `unittest` framework rather than pytest or another third-party testing framework.

---

## Project Structure

```text
engineering_team/
│
├── README.md
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
├── AGENTS.md
│
├── knowledge/
│   └── user_preference.txt
│
├── src/
│   └── engineering_team/
│       ├── __init__.py
│       ├── crew.py
│       ├── main.py
│       ├── patch.py
│       │
│       ├── config/
│       │   ├── agents.yaml
│       │   └── tasks.yaml
│       │
│       └── tools/
│           ├── __init__.py
│           ├── custom_tool.py
│           └── sandbox_tools.py
│
└── sandbox/
    ├── account_model.py
    ├── app.py
    ├── design.md
    ├── share_prices.py
    ├── test_account_model.py
    ├── test_summary.md
    └── _validate.py
```

The `sandbox` directory contains files generated and tested by the engineering agents.

---

## Sandbox

The crew uses a dedicated sandbox for agent-generated code.

Before a normal crew execution, the sandbox is reset and initialized as a fresh UV project.

The sandbox setup:

1. Removes the existing sandbox.
2. Creates a new sandbox directory.
3. Initializes a UV project using Python 3.11.
4. Installs Gradio.
5. Provides the agents with sandbox tools.

The agents can then:

* List files
* Read files
* Write files
* Execute Python files

Python execution is performed inside an ephemeral Docker container.

---

## Sandbox Tools

The project provides the following custom CrewAI tools:

### List Sandbox Files

Lists the files currently available in the sandbox.

### Read Sandbox File

Reads the contents of a file from the sandbox.

### Write Sandbox File

Creates or replaces a file in the sandbox.

### Run Sandbox Python File

Runs a Python file inside the sandbox execution environment.

These tools allow the agents to collaborate through a shared filesystem.

---

## Context7 MCP

The project uses Context7 MCP to provide the Engineering Lead and Frontend Engineer with current API information.

Context7 is particularly useful for verifying the latest Gradio APIs.

The Engineering Lead uses Context7 during the design phase and provides relevant API guidance to the frontend engineer.

The project connects to:

```text
https://mcp.context7.com/mcp
```

---

## CrewAI MCP Compatibility Patch

The project contains a custom MCP compatibility patch:

```text
src/engineering_team/patch.py
```

This patch addresses a CrewAI 1.14.4 issue related to HTTPS MCP tool names being sanitized during discovery.

In particular, MCP server tools containing characters such as hyphens can become unreachable if the sanitized name is incorrectly sent back to the MCP server.

The patch preserves the original server-side tool name.

The patch is imported when the application starts:

```python
import engineering_team.patch
```

If CrewAI is upgraded in the future, verify whether this patch is still required.

---

## Technology Stack

* Python
* CrewAI
* OpenAI
* UV
* Gradio
* Context7 MCP
* Docker
* Python `unittest`

---

## Requirements

The main CrewAI project requires:

```text
Python >= 3.10 and < 3.14
```

The project uses:

```text
CrewAI 1.14.4
```

The sandbox is initialized with Python 3.11.

You also need:

* UV
* Docker
* An OpenAI API configuration required by CrewAI

---

## Installation

Clone the repository and enter the project directory:

```bash
cd engineering_team
```

Install the dependencies:

```bash
uv sync
```

Verify the Python version:

```bash
uv run python --version
```

---

## Running the Crew

Run the complete engineering workflow:

```bash
crewai run
```

Alternatively:

```bash
uv run run_crew
```

The requirements used by the crew are defined in:

```text
src/engineering_team/main.py
```

---

## Generated Artifacts

A successful run generates engineering artifacts inside the sandbox.

Typical outputs include:

```text
sandbox/
├── design.md
├── account_model.py
├── share_prices.py
├── app.py
├── _validate.py
├── test_account_model.py
└── test_summary.md
```

These files represent the outputs of the different stages of the multi-agent workflow.

---

## Other Commands

The project exposes several CrewAI commands.

### Run

```bash
crewai run
```

### Train

```bash
train <iterations> <filename>
```

### Replay

```bash
replay <task_id>
```

### Test

```bash
test <iterations> <evaluation_llm>
```

### Run With Trigger

```bash
run_with_trigger '<json-payload>'
```

---

## Configuration

### Agents

Agent configuration is stored in:

```text
src/engineering_team/config/agents.yaml
```

### Tasks

Task configuration is stored in:

```text
src/engineering_team/config/tasks.yaml
```

### Crew

The CrewAI crew definition is implemented in:

```text
src/engineering_team/crew.py
```

### Application Entry Point

The main execution logic is implemented in:

```text
src/engineering_team/main.py
```

---

## Design Philosophy

The key idea behind this project is **specialization of AI agents**.

Instead of asking a single AI agent to perform the complete software development lifecycle, the work is divided into specialized roles:

```text
                 High-Level Requirements
                          │
                          ▼
                 ┌─────────────────┐
                 │ Engineering     │
                 │ Lead            │
                 └────────┬────────┘
                          │
                       Design
                          │
                          ▼
                 ┌─────────────────┐
                 │ Backend         │
                 │ Engineer        │
                 └────────┬────────┘
                          │
                     Backend Code
                          │
                          ▼
                 ┌─────────────────┐
                 │ Frontend        │
                 │ Engineer        │
                 └────────┬────────┘
                          │
                      Gradio UI
                          │
                          ▼
                 ┌─────────────────┐
                 │ Test            │
                 │ Engineer        │
                 └────────┬────────┘
                          │
                          ▼
                    Tested System
```

This separation makes the workflow easier to understand, maintain, and extend.

---

## Example Use Case

The current crew receives requirements for a trading simulation account-management application.

For example:

```text
A user deposits $10,000.

The user buys shares.

The system tracks the holdings.

The system calculates the current portfolio value.

The system calculates profit/loss.

The system records all transactions.

The system prevents invalid transactions.
```

The Engineering Lead first designs the solution.

The Backend Engineer then implements the business logic.

The Frontend Engineer creates a Gradio interface.

Finally, the Test Engineer validates the backend through unit tests.

---

## Important Notes

This project is a demonstration of **multi-agent software engineering using CrewAI**.

The generated trading application is a simulation and is not intended to be used as a real trading or financial system.

The sandbox is reset during a normal crew execution. Therefore, manually created files inside `sandbox/` may be removed when the crew starts again.

---

## Future Improvements

Possible future enhancements include:

* Add a dedicated code-review agent
* Add a security-review agent
* Add an architecture-review agent
* Add integration testing
* Add automated Git commits
* Add CI/CD integration
* Add persistent project memory
* Add database support
* Add API generation
* Add automated documentation generation
* Add automated pull-request creation

---

## License

Add the appropriate license information here if this project is published publicly.
