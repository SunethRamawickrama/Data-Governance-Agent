# Data Governance Agent

Data Governance Agent is an **agentic data governance system** built using a **multi-agent architecture**. The system allows users to connect data sources, such as databases, file systems, and S3 buckets (future), and perform governance tasks including compliance auditing, PII detection, and natural-language querying.

The architecture consists of:

- A **main orchestrator agent**
- Multiple **sub-agents connected as tools through an MCP Server**
- Each sub-agent also has its own MCP server with tools designed specifically for its task

## Features

- Connect structured and unstructured data sources
- Perform automated data governance audits
- Detect **PII and quasi-PII data**
- Validate data sources against **federal, state, and internal policy frameworks**
- Query data sources and metadata bout them using natural language
- Generate structured governance and audit reports
- Multi-agent architecture with dynamic tool routing

## System Architecture

The system uses two execution strategies depending on the task.

### 1. Dynamic Routing for Natural Language Queries

When a user submits a natural-language query, the orchestrator agent:

1. Receives the query
2. Dynamically decides the workflow at runtime
3. Hands off the next step to the relevant sub-agent 
4. Executes the task autonomously

This allows flexible querying without requiring predefined workflows.

### 2. Deterministic Workflow for the Audit Pipeline

The audit pipeline follows a **predefined workflow**.

This approach is used because allowing an LLM to fully determine an audit workflow can introduce errors. Instead, the workflow is defined programmatically, while the LLM is used only for the tasks it performs reliably, such as classification, policy matching, and reasoning.

## Audit Workflow

### Step 0 – Framework Ingestion

The user specifies:

- The data source to audit
- The frameworks to validate the source against

Frameworks are documents that contain federal, state, or internal policy rules related to data governance and compliance.

These documents are:

1. Uploaded through the frontend
2. Processed by the Chunker in `services/RAG_services`
3. Chunked, vectorized, and stored in the vector database
4. Each chunk is assigned a hash so that if the same chunk is uploaded again, it will not be embedded twice

Once the request reaches the API, the audit pipeline begins.

### Step 1 – Source Analysis (DB Agent)

The DB agent generates a report describing the data source, including:

- Structure and schema
- Column information
- Sample values
- Metadata

### Step 2 – Data Classification (Classification Agent)

The classification agent analyzes the source report and classifies the data into:

- PII
- Quasi-PII
- Safe data that can be stored as plain text

This step produces a classification report.

### Step 3 – Policy Validation (Policy Agent)

The classification report is then passed to the policy agent. This agent queries the vector store and searches for policies related to the detected data types in the frameworks selected by the user.

**Example:**
If an internal policy document says _"all user names should be encrypted"_, but the data report shows raw values, the policy agent will mark this as a violation.

This agent also checks metadata-level violations.

**Example:**
If metadata fields such as:

- `data_retention_policy = None`
- `data source owner = None`
- `access control = all teams`

exist, and there is a policy such as _"all databases must have an owner, a data retention policy, and controlled access control"_, the agent will mark these as violations.

### Step 4 – Remediation Generation (Remediation Agent)

The remediation agent reviews all identified violations and searches the policy documents for recommended fixes.

**Example:**
If a violation is identified as _"user names stored as raw values"_, and the policy document contains a remediation such as _"all user names must be encrypted or redacted"_, the agent will add this to the remediation list.

## Future Development

A planned enhancement is to allow the system to automatically implement remediations after receiving human approval through MCP server connections.

### Step 5 – Final Report Generation

All outputs from the previous steps are combined into a single structured report that includes:

- Source analysis
- Data classification
- Policy violations
- Recommended remediations

## Architecture Overview

```
User → Frontend → API → Orchestrator Agent
                                │
                                ├── DB Agent
                                ├── Classification Agent
                                ├── Policy Agent
                                ├── Remediation Agent

```

The vector store is used by the policy and remediation agents through the RAG services and is not part of the agent layer itself.

## Project Structure

```
project-root/
│
├── agents/
│   ├── orchestrator
│   └── sub_agents
│       ├── db_agent
│       ├── classification_agent
│       ├── policy_agent
│       └── remediation_agent
│
├── mcp_connection/
│   └── mcp_client,py
|   └── server/
│        ├── db_server.py
│        ├── file_server.py
│        └── main_mcp_server.py   # exposes the sub-agents as tools to the orchestrator
│
├── services/
│   └── RAG_services/
│
├── tools/
│   └── tool_executor/
│
├── api/
├── frontend/
└── docker/
```

## Engineering Best Practices

The project follows several engineering best practices:

- Multi-agent architecture with sub-agents exposed as tools
- Tool executor layer between the agents and the MCP server
- Loosely coupled components for easier testing and debugging
- Object-oriented design principles, including:
  - Abstract classes
  - Polymorphism through function overriding
  - Design patterns such as Factory and Adapter

- Containerized components

## Future Improvements

Planned improvements include:

- Completing the frontend with an improved UI/UX
- Improving model performance
- Adding Redis caching for faster reads
- Optimizing database indexing and read/write performance for scalability
- Fixing concurrency issues that currently affect output quality in some parts of the audit pipeline
