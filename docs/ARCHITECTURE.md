# System Architecture

This document provides a comprehensive overview of the General Contractor Agent Demo system architecture, illustrating the major components and their interactions.

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Component Interaction Diagram](#component-interaction-diagram)
3. [Data Flow: User Request Lifecycle](#data-flow-user-request-lifecycle)
4. [Agent Network Architecture](#agent-network-architecture)
5. [Technology Stack](#technology-stack)

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

## Next Steps

For more detailed information, see:

- [README.md](../README.md) - Project overview and setup
- [Backend Source](../backend/) - Python backend implementation
- [Frontend Source](../frontend/src/) - React frontend implementation
- Individual agent files for tool specifications
