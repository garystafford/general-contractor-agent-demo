# Project Summary

## General Contractor Agent Demo

A comprehensive multi-agent orchestration system demonstrating construction project management using AI agents. Built with **Strands Agents** framework and **AWS Bedrock**.

---

## 🎯 Quick Links

- **[README.md](README.md)** - Main project documentation
- **[QUICKSTART.md](QUICKSTART.md)** - Start here for quick setup
- **[TESTING.md](TESTING.md)** - Complete testing guide
- **[EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)** - Execution mode details

---

## 🚀 Get Started in 30 Seconds

```bash
# Clone or navigate to the project
cd general-contractor-agent-demo

# Install dependencies
uv sync

# Run the demo (no AWS required!)
uv run python test_shed_demo.py
```

This shows simulated agent reasoning and tool calling for a complete shed construction project!

---

## 📦 What's Included

### Core Components

1. **8 Specialized Agents** - Each with domain-specific tools
   - Architect, Carpenter, Electrician, Plumber, Mason, Painter, HVAC, Roofer

2. **General Contractor Agent** - Orchestrates all specialized agents
   - Task dependency management
   - Phase-based sequencing
   - Resource coordination

3. **Task Manager** - Handles project workflow
   - Dependency tracking
   - Phase ordering
   - Status management

4. **MCP Services** - Support services
   - Materials supplier
   - Permitting system

5. **REST API** - Complete FastAPI implementation
   - Project management endpoints
   - Agent status monitoring
   - Real-time progress tracking

### Test Scripts

| Script | AWS Required? | Description |
|--------|---------------|-------------|
| `test_shed_demo.py` | ❌ No | Simulated agent output (demo) ⭐ |
| `test_shed_detailed.py` | ❌ No | Planning mode (task breakdown) |
| `test_shed_detailed.py execute` | ✅ Yes | Real AI execution |
| `test_agent.py` | ✅ Yes | Single agent test |
| `test_shed_project.py` | ❌ No | Simple planning test |

### Documentation

- **[README.md](README.md)** - Complete project documentation
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start and test overview
- **[TESTING.md](TESTING.md)** - Testing guide with all scripts
- **[EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)** - Execution mode details

---

## 🎬 Demo: Shed Construction Project

The test scripts demonstrate building a **10×12 ft storage shed** using 6 specialized agents:

### Project Specs
- **Size**: 10 ft × 12 ft × 8 ft (height)
- **Foundation**: Concrete slab (120 sq ft)
- **Structure**: Wood frame, asphalt shingle roof
- **Features**: 1 door, 1 window, electrical
- **Finish**: Exterior paint

### Task Flow (10 Tasks)

```
Task 1  → Architect: Design shed plans
Task 2  → Mason: Pour foundation
Task 3  → Carpenter: Frame walls
Task 4  → Carpenter: Build roof trusses
Task 5  → Roofer: Install roofing
Task 6  → Electrician: Wire electrical
Task 7  → Carpenter: Install siding
Task 8  → Carpenter: Install door/window
Task 9  → Painter: Paint exterior
Task 10 → Carpenter: Final walkthrough
```

### Agent Workload
- **Carpenter**: 5 tasks (framing, roof, siding, door/window, final)
- **Architect**: 1 task (design)
- **Mason**: 1 task (foundation)
- **Roofer**: 1 task (roofing)
- **Electrician**: 1 task (electrical)
- **Painter**: 1 task (paint)

---

## 💡 Key Features

### Multi-Agent Orchestration
- Central coordinator delegates tasks to specialized agents
- Agents have domain-specific tools and expertise
- Automatic task sequencing based on dependencies

### Real-Time Streaming
- Live agent reasoning display
- Tool calls shown in real-time
- Results streamed as they complete

### Task Management
- Dependency tracking (Task 2 waits for Task 1, etc.)
- Phase-based execution (Planning → Foundation → Framing → etc.)
- Parallel execution when dependencies allow

### Project Types Supported
1. `kitchen_remodel` - Kitchen renovation
2. `bathroom_remodel` - Bathroom renovation
3. `new_construction` - New building
4. `addition` - Home addition
5. `shed_construction` - Storage shed (demo) ⭐

---

## 🛠️ Technical Stack

- **Framework**: Strands Agents SDK
- **AI Model**: Claude (via AWS Bedrock)
- **Backend**: Python 3.13+, FastAPI
- **Package Manager**: uv
- **Agent Tools**: Pydantic-based tool definitions
- **Streaming**: Async/await with real-time events

---

## 📊 Architecture

```
┌─────────────────────────────────────────┐
│     General Contractor Agent            │
│         (Orchestrator)                   │
└───────────────┬─────────────────────────┘
                │
    ┌───────────┴───────────┐
    │                       │
┌───▼────┐            ┌────▼─────┐
│ Task   │            │ Agents   │
│Manager │            │ Pool     │
└───┬────┘            └────┬─────┘
    │                      │
    │     ┌────────────────┼─────────┐
    │     │                │         │
┌───▼─────▼───┐   ┌───────▼──┐  ┌──▼──────┐
│ Architect   │   │Carpenter │  │Electrician│
│ Plumber     │   │  Mason   │  │  Painter │
│ HVAC        │   │  Roofer  │  │          │
└─────────────┘   └──────────┘  └──────────┘
        │                │
        └────────┬───────┘
                 │
        ┌────────▼──────────┐
        │  MCP Services     │
        │  - Materials      │
        │  - Permitting     │
        └───────────────────┘
```

---

## 🎓 Educational Value

This project demonstrates:

1. **Agent Orchestration** - Central coordinator pattern
2. **Tool Use** - Agents using specialized functions
3. **Task Dependencies** - Sequential and parallel execution
4. **State Management** - Tracking project and task states
5. **Streaming Output** - Real-time agent reasoning
6. **Error Handling** - Graceful failure management
7. **Domain Modeling** - Construction workflow in AI

---

## 🔧 Configuration

### AWS Bedrock Setup

1. Enable Claude model access in AWS Bedrock Console
2. Get model ID (e.g., `us.anthropic.claude-sonnet-4-5-v1:0`)
3. Configure credentials in `.env`:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_SESSION_TOKEN=your_token  # Optional

# Or use profile
AWS_PROFILE=default

# Model ID (get from AWS Console)
DEFAULT_MODEL=us.anthropic.claude-sonnet-4-5-v1:0
```

### Testing Without AWS

You can explore the system without AWS credentials:

```bash
# Demo with simulated output
uv run python test_shed_demo.py

# Planning mode
uv run python test_shed_detailed.py
```

---

## 📈 Performance

### Demo Mode
- **Duration**: 30 seconds
- **Cost**: Free (simulated)
- **Output**: Realistic agent interactions

### Execution Mode (with AWS)
- **Duration**: 5-10 minutes (10 tasks)
- **Cost**: ~$0.10-0.50 per full project
- **Output**: Real Claude AI reasoning

Per task:
- Input tokens: ~2,000
- Output tokens: ~500-1,000
- Duration: 30-60 seconds

---

## 🚦 Getting Started Roadmap

### Level 1: No AWS Setup
```bash
uv run python test_shed_demo.py
```
See simulated agent output with detailed reasoning.

### Level 2: Planning & Structure
```bash
uv run python test_shed_detailed.py
```
Understand task dependencies and project flow.

### Level 3: AWS Configuration
1. Set up AWS Bedrock
2. Configure `.env`
3. Test single agent

### Level 4: Full Execution
```bash
uv run python test_shed_detailed.py execute
```
Watch real Claude AI agents build the shed!

---

## 🤝 Support

- **Issues**: Open an issue on GitHub
- **Documentation**: See [README.md](README.md)
- **Quick Start**: See [QUICKSTART.md](QUICKSTART.md)
- **Testing**: See [TESTING.md](TESTING.md)

---

## 📝 License

Educational and training purposes.

---

## 🙏 Acknowledgments

- Built with [Strands Agents](https://strandsagents.com/latest/)
- Powered by Claude via AWS Bedrock
- Inspired by real-world construction management
- Demonstrates multi-agent orchestration patterns

---

**Ready to get started?** Run `uv run python test_shed_demo.py` now!
