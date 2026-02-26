# System Architecture

This document provides a comprehensive overview of the General Contractor Agent Demo system architecture, illustrating the major components and their interactions.

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Component Interaction Diagram](#component-interaction-diagram)
3. [Data Flow: User Request Lifecycle](#data-flow-user-request-lifecycle)
4. [Agent Network Architecture](#agent-network-architecture)
5. [Technology Stack](#technology-stack)
6. [Design Philosophy](#design-philosophy)

---

## System Architecture Overview

This diagram shows the layered architecture of the system, from the user interface down to external services.

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React UI]
        PF[ProjectForm]
        DB[Dashboard]
        HC[HealthCheck]
        AG[AgentNetworkGraph]
        Store[Zustand Store]
        API[API Client<br/>Axios]
        WS[WebSocket Hooks]
    end

    subgraph "API Layer"
        FastAPI[FastAPI Server<br/>routes.py]
        CORS[CORS Middleware]
        WSM[WebSocket Manager]
        Pydantic[Pydantic Validation]
    end

    subgraph "Orchestration Layer"
        GC[General Contractor<br/>Orchestrator Agent]
        TM[Task Manager<br/>Dependencies & Sequencing]
        PP[Project Planner<br/>Dynamic Planning]
        LD[Loop Detection]
    end

    subgraph "Agent Layer"
        Arch[Architect Agent]
        Carp[Carpenter Agent]
        Elec[Electrician Agent]
        Plumb[Plumber Agent]
        Mason[Mason Agent]
        Paint[Painter Agent]
        HVAC[HVAC Agent]
        Roof[Roofer Agent]
    end

    subgraph "MCP Services Layer"
        MCP1[Materials Supplier<br/>MCP Server]
        MCP2[Permitting Service<br/>MCP Server]
    end

    subgraph "External Services"
        Bedrock[AWS Bedrock<br/>Claude LLM]
    end

    UI --> PF & DB & HC & AG
    PF --> Store
    DB --> Store
    Store --> API
    DB --> WS
    API --> FastAPI
    WS --> WSM
    FastAPI --> CORS & Pydantic & WSM
    FastAPI --> GC
    GC --> TM & PP & LD
    GC --> Arch & Carp & Elec & Plumb & Mason & Paint & HVAC & Roof
    GC -.->|stdio| MCP1 & MCP2
    Arch & Carp & Elec & Plumb & Mason & Paint & HVAC & Roof --> Bedrock

    style UI fill:#e1f5ff
    style FastAPI fill:#fff4e1
    style GC fill:#ffe1f5
    style Bedrock fill:#e1ffe1
    style MCP1 fill:#f5e1ff
    style MCP2 fill:#f5e1ff
```

---

## Component Interaction Diagram

This diagram illustrates the detailed connections and communication protocols between components.

```mermaid
graph LR
    subgraph "Browser"
        User((User))
        React[React App<br/>Vite]
    end

    subgraph "Backend Server"
        API[FastAPI<br/>:8000]

        subgraph "General Contractor"
            GC[Orchestrator]
            AgentPool[Agent Pool<br/>8 Trade Agents]
            MCPClient[MCP Client]
        end

        TM[Task Manager]

        subgraph "Trade Agents"
            A1[Architect]
            A2[Carpenter]
            A3[Electrician]
            A4[Plumber]
            A5[Mason]
            A6[Painter]
            A7[HVAC]
            A8[Roofer]
        end
    end

    subgraph "MCP Servers"
        MS[Materials Supplier<br/>stdio process]
        PS[Permitting Service<br/>stdio process]
    end

    subgraph "AWS"
        Bedrock[Bedrock API<br/>Claude Sonnet]
    end

    User -->|HTTP/WS| React
    React -->|REST API<br/>localhost:8000| API
    React -.->|WebSocket<br/>/ws/*| API

    API --> GC
    GC --> TM
    GC --> AgentPool
    AgentPool --> A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8

    GC --> MCPClient
    MCPClient -->|stdio<br/>MCP Protocol| MS
    MCPClient -->|stdio<br/>MCP Protocol| PS

    A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 -->|boto3<br/>Bedrock Runtime| Bedrock

    style User fill:#4CAF50
    style React fill:#61dafb
    style API fill:#009688
    style GC fill:#ff6b6b
    style Bedrock fill:#FF9800
    style MS fill:#9C27B0
    style PS fill:#9C27B0
```

---

## Data Flow: User Request Lifecycle

This sequence diagram shows the complete lifecycle of a project execution request.

```mermaid
sequenceDiagram
    actor User
    participant UI as React UI
    participant API as FastAPI
    participant GC as General Contractor
    participant TM as Task Manager
    participant Agent as Trade Agent
    participant MCP as MCP Server
    participant Bedrock as AWS Bedrock

    User->>UI: Submit Project<br/>(Kitchen Remodel)
    UI->>API: POST /api/projects/start
    API->>GC: start_project()
    GC->>TM: create_tasks()
    TM->>TM: Generate task breakdown<br/>with dependencies
    TM-->>GC: Return task list
    GC-->>API: Project created
    API-->>UI: 200 OK + task data
    UI->>UI: Navigate to Dashboard

    User->>UI: Click "Execute All"
    UI->>API: POST /api/projects/execute-all

    loop For each phase
        API->>GC: execute_next_phase()
        GC->>TM: get_ready_tasks()
        TM-->>GC: Tasks with dependencies met

        loop For each ready task
            GC->>GC: Mark task IN_PROGRESS
            GC->>Agent: delegate_task(task)
            Agent->>Bedrock: invoke_model()<br/>with tools
            Bedrock-->>Agent: Tool calls needed

            alt Agent Tool
                Agent->>Agent: execute_tool()
                Agent-->>Agent: Tool result
            else MCP Tool
                Agent->>GC: Request MCP tool
                GC->>MCP: call_tool_async()
                MCP-->>GC: Tool result
                GC-->>Agent: Tool result
            end

            Agent->>Bedrock: Continue with results
            Bedrock-->>Agent: Final response
            Agent-->>GC: Task complete
            GC->>TM: Mark task COMPLETED
        end
    end

    GC-->>API: Project complete
    API-->>UI: 200 OK

    loop Dashboard polling
        UI->>API: GET /api/projects/status
        API-->>UI: Current status
        UI->>API: GET /api/tasks
        API-->>UI: Task list
        UI->>UI: Update progress bars
    end
```

---

## Agent Network Architecture

This diagram shows the relationships between agents and their specialized tools.

```mermaid
graph TB
    GC[General Contractor<br/>Orchestrator]

    subgraph "Planning & Coordination"
        PP[Project Planner Agent<br/>- analyze_project_scope<br/>- generate_task_breakdown<br/>- validate_dependencies<br/>- assign_phases]
        Arch[Architect Agent<br/>- create_design_plans<br/>- review_specifications<br/>- coordinate_inspections]
    end

    subgraph "Foundation & Structure"
        Mason[Mason Agent<br/>- pour_concrete<br/>- lay_bricks<br/>- build_foundation]
        Carp[Carpenter Agent<br/>- frame_walls<br/>- install_doors<br/>- build_cabinets<br/>- install_wood_flooring<br/>- hang_drywall]
    end

    subgraph "Systems Installation"
        Elec[Electrician Agent<br/>- install_wiring<br/>- install_outlets<br/>- install_light_fixtures<br/>- install_breaker_panel]
        Plumb[Plumber Agent<br/>- install_pipes<br/>- install_fixtures<br/>- pressure_test]
        HVAC[HVAC Agent<br/>- install_ductwork<br/>- install_hvac_unit<br/>- test_system]
    end

    subgraph "Finishing & Exterior"
        Paint[Painter Agent<br/>- prepare_surfaces<br/>- apply_primer<br/>- apply_paint]
        Roof[Roofer Agent<br/>- install_roofing<br/>- install_gutters<br/>- waterproof]
    end

    subgraph "External Services (MCP)"
        Mat[Materials Supplier<br/>- get_catalog<br/>- check_availability<br/>- order_materials<br/>- get_order]
        Perm[Permitting Service<br/>- apply_for_permit<br/>- check_permit_status<br/>- schedule_inspection<br/>- get_required_permits]
    end

    GC -->|delegates tasks| PP & Arch
    GC -->|delegates tasks| Mason & Carp
    GC -->|delegates tasks| Elec & Plumb & HVAC
    GC -->|delegates tasks| Paint & Roof
    GC -->|MCP Protocol| Mat & Perm

    Arch -->|coordinates with| Mason & Carp & Elec & Plumb & HVAC & Roof
    Mason -->|foundation for| Carp
    Carp -->|framing for| Elec & Plumb & HVAC & Roof
    Elec & Plumb & HVAC -->|rough-in before| Paint
    Roof -->|weatherproofing before| Paint

    style GC fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style PP fill:#4dabf7,stroke:#1971c2
    style Arch fill:#4dabf7,stroke:#1971c2
    style Mason fill:#ffd43b,stroke:#f59f00
    style Carp fill:#ffd43b,stroke:#f59f00
    style Elec fill:#74c0fc,stroke:#339af0
    style Plumb fill:#74c0fc,stroke:#339af0
    style HVAC fill:#74c0fc,stroke:#339af0
    style Paint fill:#b2f2bb,stroke:#51cf66
    style Roof fill:#b2f2bb,stroke:#51cf66
    style Mat fill:#e599f7,stroke:#cc5de8
    style Perm fill:#e599f7,stroke:#cc5de8
```

---

## Orchestration Model: Code vs. LLM

A key architectural distinction: the **General Contractor is NOT an LLM agent**. It is a deterministic Python execution loop that makes zero Bedrock API calls. Only the Project Planner and the 8 trade agents are LLM-powered.

This "plan-then-execute" pattern means the LLM generates the task graph, then deterministic code executes it.

```mermaid
graph TB
    subgraph "API Layer"
        API[FastAPI<br/>routes.py]
    end

    subgraph "Code-Based Orchestration  (No LLM Calls)"
        direction TB
        GC["General Contractor<br/><i>Python execution loop</i><br/>execute_entire_project()"]
        TM["Task Manager<br/><i>Dependency resolution</i><br/>get_ready_tasks()"]
        LP["Loop & Timeout Protection<br/><i>asyncio.wait_for()</i>"]
    end

    subgraph "LLM-Powered Agents  (Bedrock API Calls)"
        PP["Project Planner<br/><i>Strands Agent</i><br/>Only for custom projects"]
        Agents["Trade Agents × 8<br/><i>Strands Agents</i><br/>Architect, Carpenter,<br/>Electrician, Plumber,<br/>Mason, Painter, HVAC, Roofer"]
    end

    subgraph "External"
        Bedrock[AWS Bedrock<br/>Claude LLM]
        MCP1[Materials MCP]
        MCP2[Permitting MCP]
    end

    API -->|"start_project()"| GC
    GC -->|"Phase 0: Plan<br/>(custom projects only)"| PP
    PP -->|"Returns task graph"| GC
    GC <-->|"get_ready_tasks()<br/>mark_completed()"| TM
    GC -->|"Phase 1-N: Execute<br/>delegate_task()"| Agents
    GC --- LP

    PP -->|"invoke_async()"| Bedrock
    Agents -->|"invoke_async()"| Bedrock
    GC -.->|"MCP Protocol"| MCP1 & MCP2

    style GC fill:#4a90d9,stroke:#2a6cb8,color:#fff
    style TM fill:#4a90d9,stroke:#2a6cb8,color:#fff
    style LP fill:#4a90d9,stroke:#2a6cb8,color:#fff
    style PP fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style Agents fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style Bedrock fill:#FF9800,stroke:#e65100,color:#fff
    style MCP1 fill:#9C27B0,stroke:#6a1b9a,color:#fff
    style MCP2 fill:#9C27B0,stroke:#6a1b9a,color:#fff
```

**Legend:** Blue = deterministic Python code (no LLM). Red = LLM-powered Strands agents (Bedrock API calls).

### Why No LLM Orchestrator?

| Aspect             | Code Orchestrator (Current)     | LLM Orchestrator (Alternative)   |
| ------------------ | ------------------------------- | -------------------------------- |
| **Cost**           | $0 for orchestration            | Extra Bedrock calls per decision |
| **Speed**          | Instant task dispatch           | Seconds of LLM latency per step  |
| **Reliability**    | Deterministic, no hallucination | May hallucinate or loop          |
| **Token Usage**    | Zero orchestration tokens       | Significant token overhead       |
| **Predictability** | Same input = same execution     | May vary between runs            |

The General Contractor appears in no token usage reports because it makes zero LLM calls. All Bedrock API calls come from the Project Planner (for custom projects) and the 8 trade agents.

### Example Task Graph: Shed Construction

This is the actual dependency graph produced by the shed construction template. Each node is a task; arrows show "must complete before" dependencies. The General Contractor walks this graph using `get_ready_tasks()`, executing tasks whose dependencies are all satisfied.

```mermaid
graph TD
    T1["1 · Architect<br/>Design shed plans"]
    T2["2 · Mason<br/>Pour concrete foundation"]
    T3["3 · Carpenter<br/>Frame walls & openings"]
    T4["4 · Carpenter<br/>Build roof trusses"]
    T5["5 · Roofer<br/>Install shingles & underlayment"]
    T6["6 · Carpenter<br/>Install exterior siding"]
    T7["7 · Carpenter<br/>Install door & window"]
    T8["8 · Painter<br/>Paint exterior finish"]
    T9["9 · Carpenter<br/>Final walkthrough & cleanup"]

    T1 -->|"plan done"| T2
    T2 -->|"foundation set"| T3
    T3 -->|"walls up"| T4
    T4 -->|"trusses up"| T5
    T5 -->|"roof done"| T6
    T6 -->|"siding on"| T7
    T7 -->|"doors/windows in"| T8
    T8 -->|"paint dry"| T9

    style T1 fill:#4dabf7,stroke:#1971c2,color:#fff
    style T2 fill:#ffd43b,stroke:#f59f00
    style T3 fill:#ffd43b,stroke:#f59f00
    style T4 fill:#ffd43b,stroke:#f59f00
    style T5 fill:#74c0fc,stroke:#339af0
    style T6 fill:#b2f2bb,stroke:#51cf66
    style T7 fill:#b2f2bb,stroke:#51cf66
    style T8 fill:#b2f2bb,stroke:#51cf66
    style T9 fill:#e599f7,stroke:#cc5de8
```

**Phases:** Blue = planning, Yellow = foundation/framing, Light blue = rough-in, Green = finishing, Purple = final inspection.

The TaskManager resolves this graph at runtime: task 3 won't start until task 2 is marked complete, task 5 won't start until task 4 is done, and so on. For projects with parallel branches (e.g., electrical and plumbing rough-in happening simultaneously), multiple tasks can be ready at the same time.

### Execution Flow

```text
Template Project                    Custom Project
──────────────                      ──────────────
1. API receives request             1. API receives request
2. GC loads hardcoded template      2. GC invokes Project Planner (LLM)
   (no LLM call)                       → Planner returns task graph
3. TaskManager builds task graph    3. TaskManager builds task graph
4. GC execution loop:               4. GC execution loop:
   ├─ get_ready_tasks()                ├─ get_ready_tasks()
   ├─ delegate to trade agent (LLM)    ├─ delegate to trade agent (LLM)
   ├─ mark_completed()                 ├─ mark_completed()
   └─ repeat until done                └─ repeat until done
```

---

## Technology Stack

### Frontend Stack

```mermaid
graph LR
    subgraph "Frontend Technologies"
        React[React 18<br/>UI Framework]
        TS[TypeScript<br/>Type Safety]
        Vite[Vite<br/>Build Tool]
        Zustand[Zustand<br/>State Management]
        RR[React Router 7<br/>Routing]
        Axios[Axios<br/>HTTP Client]
        TW[Tailwind CSS<br/>Styling]
        XY[XYFlow<br/>Graph Visualization]
    end

    React --> TS & Zustand & RR & TW
    Axios --> React
    XY --> React
    Vite --> React

    style React fill:#61dafb,stroke:#0088cc
    style TS fill:#3178c6,stroke:#235a97,color:#fff
    style Vite fill:#646cff,stroke:#535bf2,color:#fff
    style Zustand fill:#443e38,stroke:#2d2926,color:#fff
    style TW fill:#38bdf8,stroke:#0ea5e9
```

### Backend Stack

```mermaid
graph LR
    subgraph "Backend Technologies"
        Python[Python 3.11+<br/>Runtime]
        FastAPI[FastAPI<br/>Web Framework]
        Strands[Strands Agents<br/>Agent Framework]
        MCP[MCP SDK<br/>Model Context Protocol]
        Pydantic[Pydantic<br/>Validation]
        Boto3[Boto3<br/>AWS SDK]
        Bedrock[Amazon Bedrock<br/>Claude Sonnet 4]
    end

    Python --> FastAPI & Strands & MCP & Pydantic & Boto3
    Strands --> Bedrock
    Boto3 --> Bedrock

    style Python fill:#3776ab,stroke:#2b5b84,color:#fff
    style FastAPI fill:#009688,stroke:#00695c,color:#fff
    style Strands fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style MCP fill:#9C27B0,stroke:#6a1b9a,color:#fff
    style Bedrock fill:#FF9800,stroke:#e65100,color:#fff
```

### Architecture Patterns

| Layer                 | Pattern                      | Purpose                                       |
| --------------------- | ---------------------------- | --------------------------------------------- |
| **Frontend**          | Component-based architecture | Modular, reusable UI components               |
| **State**             | Centralized store (Zustand)  | Single source of truth for application state  |
| **API**               | RESTful + WebSocket          | Synchronous requests + real-time updates      |
| **Orchestration**     | Coordinator pattern          | Central agent delegates to specialized agents |
| **Task Management**   | Dependency resolution        | Ensures tasks execute in correct order        |
| **Agents**            | Tool-calling pattern         | LLM agents with specialized capabilities      |
| **External Services** | MCP Protocol                 | Standardized AI-to-service communication      |
| **Error Handling**    | Loop detection + timeouts    | Prevents infinite loops and runaway processes |

---

## Key Features

### Multi-Agent Coordination

- **8 specialized trade agents** each with domain-specific tools
- **Central orchestrator** (General Contractor) manages delegation
- **Task dependency resolution** ensures correct execution order
- **Phase-based sequencing** mirrors real construction workflows

### External Service Integration

- **MCP (Model Context Protocol)** for standardized service communication
- **Materials Supplier** for inventory and ordering
- **Permitting Service** for compliance and inspections
- **Stdio transport** for process isolation

### Planning Strategies

The system uses two different planning approaches depending on the project type:

#### Template-Based Planning (Default)

For common project types, the system uses predefined task templates that don't require LLM planning:

| Project Type | Planning Mode | Project Planner Used? |
|--------------|---------------|----------------------|
| Kitchen Remodel | Template | No |
| Bathroom Remodel | Template | No |
| Shed Construction | Template | No |
| New Construction | Template | No |
| Home Addition | Template | No |

Template-based planning is faster and more cost-effective since it skips the LLM planning step.

#### Dynamic LLM-Powered Planning

For custom or unusual projects, the **Project Planner Agent** is invoked to dynamically generate a task breakdown:

| Project Type | Planning Mode | Project Planner Used? |
|--------------|---------------|----------------------|
| Custom Project | Dynamic | Yes |
| Dog House | Dynamic | Yes |
| Treehouse | Dynamic | Yes |
| Home Theater | Dynamic | Yes |
| Any non-template type | Dynamic | Yes |

The Project Planner Agent uses Claude to:
1. Analyze project scope and requirements
2. Generate a detailed task breakdown
3. Validate task dependencies
4. Assign construction phases
5. Finalize the executable plan

**Note:** If you don't see the Project Planner node active in the Agent Network Graph, it's likely because you're running a template-based project. To see the Project Planner in action, start a custom project or use a project type without a predefined template.

#### Validation Layer

Both planning modes include validation to ensure all required information is provided before execution begins.

### Real-time Monitoring

- **WebSocket support** for live updates (optional)
- **Polling fallback** for simpler deployment
- **Comprehensive health checks** for all system components
- **Agent activity tracking** shows which agents are active

### Error Recovery

- **Loop detection** prevents infinite tool calling
- **Task timeouts** prevent runaway executions
- **Skip/retry functionality** for stuck or failed tasks
- **Detailed error reporting** with actionable suggestions

---

## Communication Protocols

| Protocol                | Usage                        | Components                       |
| ----------------------- | ---------------------------- | -------------------------------- |
| **HTTP REST**           | Synchronous API calls        | Frontend ↔ Backend               |
| **WebSocket**           | Real-time updates (optional) | Frontend ↔ Backend               |
| **MCP over stdio**      | External service tool calls  | General Contractor ↔ MCP Servers |
| **Bedrock Runtime API** | LLM inference                | Agents ↔ AWS Bedrock             |
| **boto3**               | AWS service communication    | Backend ↔ AWS                    |

---

## Deployment Architecture

### Local Development (Without Docker)

```mermaid
graph TB
    subgraph "Local Development"
        Dev[Developer Machine]

        subgraph "Frontend Process"
            Vite[Vite Dev Server<br/>:5173]
        end

        subgraph "Backend Process"
            Uvicorn[Uvicorn<br/>FastAPI :8000]
            MCP1[Materials MCP<br/>stdio subprocess]
            MCP2[Permitting MCP<br/>stdio subprocess]
        end
    end

    subgraph "AWS Cloud"
        Bedrock[Amazon Bedrock<br/>Claude Sonnet 4]
    end

    Dev --> Vite & Uvicorn
    Vite -->|proxy :8000| Uvicorn
    Uvicorn --> MCP1 & MCP2
    Uvicorn -->|boto3 + credentials| Bedrock

    style Vite fill:#646cff,color:#fff
    style Uvicorn fill:#009688,color:#fff
    style MCP1 fill:#9C27B0,color:#fff
    style MCP2 fill:#9C27B0,color:#fff
    style Bedrock fill:#FF9800,color:#fff
```

### Docker Deployment

```mermaid
graph TB
    subgraph "Docker Compose"
        subgraph "gc-frontend Container"
            Nginx[nginx:80<br/>React SPA]
        end

        subgraph "gc-backend Container"
            FastAPI[FastAPI:8000]
            MCP1[Materials MCP<br/>stdio subprocess]
            MCP2[Permitting MCP<br/>stdio subprocess]
        end
    end

    subgraph "Host Machine"
        Port3000[localhost:3000]
        Port8000[localhost:8000]
    end

    subgraph "AWS Cloud"
        Bedrock[Amazon Bedrock<br/>Claude Sonnet 4]
    end

    Port3000 --> Nginx
    Port8000 --> FastAPI
    Nginx -->|API calls| FastAPI
    FastAPI --> MCP1 & MCP2
    FastAPI -->|boto3 + credentials| Bedrock

    style Nginx fill:#009639,color:#fff
    style FastAPI fill:#009688,color:#fff
    style MCP1 fill:#9C27B0,color:#fff
    style MCP2 fill:#9C27B0,color:#fff
    style Bedrock fill:#FF9800,color:#fff
```

**Docker containers:**

| Container      | Image            | Port       | Purpose                |
| -------------- | ---------------- | ---------- | ---------------------- |
| `gc-frontend`  | nginx:alpine     | 3000 → 80  | Serves React SPA       |
| `gc-backend`   | python:3.13-slim | 8000       | FastAPI + Agents + MCP |

See [DOCKER.md](DOCKER.md) for complete Docker deployment guide.

---

## File Structure

```text
general-contractor-agent-demo/
├── backend/
│   ├── agents/
│   │   ├── general_contractor.py    # Main orchestrator
│   │   ├── project_planner.py       # Dynamic planning agent
│   │   ├── architect.py              # Design & planning
│   │   ├── carpenter.py              # Framing & woodwork
│   │   ├── electrician.py            # Electrical systems
│   │   ├── plumber.py                # Plumbing systems
│   │   ├── mason.py                  # Foundation & masonry
│   │   ├── painter.py                # Finishing work
│   │   ├── hvac.py                   # HVAC systems
│   │   └── roofer.py                 # Roofing & weatherproofing
│   ├── mcp_servers/
│   │   ├── materials_supplier.py     # Materials MCP server
│   │   └── permitting.py             # Permitting MCP server
│   ├── orchestration/
│   │   └── task_manager.py           # Task dependency management
│   ├── api/
│   │   └── routes.py                 # FastAPI routes
│   ├── utils/
│   │   └── loop_detection.py         # Loop prevention
│   └── config.py                     # Configuration
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ProjectForm.tsx       # Project submission
│       │   ├── Dashboard.tsx         # Main dashboard (WebSocket)
│       │   ├── DashboardSimple.tsx   # Polling dashboard
│       │   ├── AgentNetworkGraph.tsx # Visual agent graph
│       │   ├── HealthCheck.tsx       # System health
│       │   └── ErrorModal.tsx        # Error display
│       ├── api/
│       │   └── client.ts             # API client
│       ├── store/
│       │   └── projectStore.ts       # Zustand state
│       ├── hooks/
│       │   └── useWebSocket.ts       # WebSocket hook
│       └── App.tsx                   # Root component
└── docs/
    └── architecture.md               # This file
```

---

## Design Philosophy

### Plan-Then-Execute with Code-Based Orchestration

This project follows a **plan-then-execute** architecture: an LLM generates the task graph (the "what"), then deterministic Python code orchestrates execution (the "how"). This is a deliberate separation of concerns - intelligence is used where it adds value (planning, domain reasoning) and avoided where it adds cost without benefit (sequencing, dependency resolution).

The pattern has deep roots:

- **Classical AI planning** (1970s+) established the principle of separating plan generation from plan execution. Systems like STRIPS and HTN (Hierarchical Task Networks) generated action sequences that were then executed by deterministic interpreters.
- **Workflow engines** like Apache Airflow, Prefect, and Dagster popularized DAG-based task orchestration in software engineering - define a dependency graph, then a scheduler walks it.
- **Modern LLM agent frameworks** have adopted similar patterns. LangGraph's "Plan-and-Execute" agent, ReWOO (Reasoning WithOut Observation), and Strands Agents' own workflow pattern all separate planning from execution to reduce LLM calls and improve reliability.

### Why This Approach

The alternative - using an LLM as the orchestrator (as CrewAI and AutoGen do) - would mean every scheduling decision requires a Bedrock API call. For a 10-task project, that's 10+ extra LLM round-trips just to decide "what runs next," a question the dependency graph already answers deterministically.

The code-based orchestrator provides:

- **Zero orchestration cost** - No Bedrock calls for task dispatch
- **Deterministic behavior** - Same project = same execution order, every time
- **No orchestration hallucination** - The scheduler can't "forget" a dependency or invent tasks
- **Sub-millisecond dispatch** - No LLM latency between tasks

Intelligence is concentrated where it matters:

- **Project Planner agent** - Uses LLM to generate task breakdowns for novel project types (dynamic DAG creation)
- **Trade agents** - Use LLM to reason about domain-specific work, call tools, and produce detailed results
- **MCP servers** - Provide structured access to external services (materials, permits)

### Domain Fit

Construction maps naturally to DAG-based execution because real-world construction has strict physical dependency ordering: you cannot install roofing before framing, you cannot paint before drywall. These constraints are inherent to the domain, not arbitrary - making a dependency graph the right abstraction.

The construction metaphor also maps well to multi-agent specialization. Real construction crews have distinct trades (electrician, plumber, carpenter) that work independently within their domain but coordinate through a general contractor. This project mirrors that structure directly.

### Hybrid Planning

The system uses a pragmatic hybrid:

- **Template-based planning** for known project types (kitchen remodel, shed, etc.) - instant, free, predictable
- **LLM-based dynamic planning** for arbitrary project types - flexible, uses Claude's construction knowledge to generate novel task graphs

This avoids the false choice between "hard-coded only" and "LLM for everything." Templates handle the common case efficiently; the LLM handles the long tail of custom projects.

---

## Next Steps

For more detailed information, see:

- [README.md](../README.md) - Project overview and setup
- [Backend Source](../backend/) - Python backend implementation
- [Frontend Source](../frontend/src/) - React frontend implementation
- Individual agent files for tool specifications
