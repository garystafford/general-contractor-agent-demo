# Changelog

This document tracks all major changes, improvements, and features added to the General Contractor Agent Demo project across development sessions.

---

## Session 4: UX & Polish (November 22, 2025)

### 🎨 Dynamic Planning UI Clarity

- **Added interactive Info button** with expandable help section explaining dynamic planning
- **Improved checkbox label**: Changed from "Use AI-powered dynamic planning instead of template" to "Generate custom AI plan (instead of using standard template)"
- **Added comparison table**: Side-by-side view of Standard Template vs. Dynamic Planning features
- **Enhanced loading states**: Shows "Generating AI Project Plan..." when using dynamic planning
- **Improved success messages**: Confirms which planning method was used
- **Updated documentation section**: Enhanced "How it works" with planning method explanations

**Files Modified**: `frontend/src/components/ProjectForm.tsx`

---

### ⚙️ Configurable UI Refresh Interval

- **Created frontend config system**: New `frontend/src/config.ts` file
- **Added environment variable**: `VITE_UI_REFRESH_INTERVAL_MS` for frontend
- **Changed default**: From 1 second to 3 seconds (reduced load)
- **Created frontend .env.example**: Template for frontend configuration
- **Dynamic display**: Auto-refresh indicator now shows actual configured interval
- **Updated backend .env.example**: Added UI_REFRESH_INTERVAL_MS configuration

**Files Created**: `frontend/src/config.ts`, `frontend/.env.example`
**Files Modified**: `.env.example`, `frontend/src/components/DashboardSimple.tsx`

---

### 🤖 Fully Autonomous Execution

- **Auto-execute on project start**: Projects now run autonomously without manual intervention
- **Removed manual buttons**: Deleted "Execute All" and "Next Phase" buttons from dashboard header
- **Removed "Action Required" banner**: No more confusing "Project Paused" warnings
- **Added autonomous status indicators**:
  - "🤖 Autonomous Execution in Progress" during execution
  - "✅ Project Complete!" when finished
- **Streamlined dashboard**: Only Refresh and Reset buttons remain
- **Improved execution flow**: Navigate → Auto-execute in background

**Files Modified**: `frontend/src/components/ProjectForm.tsx`, `frontend/src/components/DashboardSimple.tsx`

---

### 🐛 Critical Bug Fixes

#### Fixed Execution Stopping Bug (87.5% Issue)

- **Problem**: `execute_entire_project()` would stop when encountering "waiting" status, leaving projects incomplete
- **Solution**: Added intelligent waiting logic that continues execution when tasks are in progress
- **Added deadlock detection**: Breaks only on true dependency deadlocks
- **Result**: Projects now complete to 100% autonomously

**Files Modified**: `backend/agents/general_contractor.py:615-634`

#### Fixed Phase Progression Visualization

- **Problem**: Phase progress bar showed all gray or incorrect colors
- **Solution**:
  - Added phase normalization to map non-standard phases ("construction" → "framing")
  - Fixed logic to show all phases green when 100% complete
  - Phases now correctly transition: gray → blue (current) → green (completed)
- **Added phase mapping**: Handles dynamic planning's varied phase names

**Files Modified**: `frontend/src/components/DashboardSimple.tsx:181-203`

#### Fixed Navigation Flow

- **Problem**: Form submission wouldn't navigate to dashboard automatically
- **Solution**: Improved navigation timing and state cleanup
- **Added debugging**: Console logs for troubleshooting

**Files Modified**: `frontend/src/components/ProjectForm.tsx`

---

### 👁️ Enhanced Task Visibility

- **Added PENDING status display**: Gray cards showing tasks waiting for dependencies
- **Added BLOCKED status display**: Purple cards showing tasks that can't proceed
- **Updated activity feed header**: Shows all 6 task states (active, failed, completed, queued, pending, blocked)
- **Reordered task display**: Better UX with logical ordering:
  1. In Progress (blue, animated)
  2. Ready (yellow)
  3. Pending (gray)
  4. Blocked (purple)
  5. Completed (green, newest first)
  6. Failed (red, with Skip/Retry buttons)
- **Added code comments**: Clear section markers for each task status

**Files Modified**: `frontend/src/components/DashboardSimple.tsx`

---

### 🏥 Backend Health Check System

- **Added startup health check**: Verifies backend is running before loading app
- **Loading state**: Shows "Connecting to backend..." during check
- **Error screen**: Clear instructions if backend is unavailable
  - Shows backend URL
  - Displays start command: `python start.py`
  - "Retry Connection" button
- **Prevents confusing errors**: Users know immediately if backend is down

**Files Created**: N/A (used existing `/health` endpoint)
**Files Modified**: `frontend/src/App.tsx`, `frontend/src/api/client.ts`

---

### 🧹 ESLint Setup & Code Quality

- **Installed ESLint**: With TypeScript and React plugins
- **Created ESLint config**: `.eslintrc.json` with recommended rules
- **Added npm scripts**:
  - `npm run lint` - Check for issues
  - `npm run lint:fix` - Auto-fix issues
- **Fixed 19 linting issues**:
  - Removed unused error variables in catch blocks
  - Removed unused handler functions (`handleExecuteNextPhase`, `handleExecuteAll`)
  - Removed unused state variables (`isExecuting`, `executionMode`)
  - Removed unused imports
- **Reduced errors**: From 39 to 20 (remaining are acceptable `any` types)

**Files Created**: `frontend/.eslintrc.json`
**Files Modified**: `frontend/package.json`, multiple component files

---

### 📚 Documentation Improvements

- **Created EXAMPLE_PROJECTS.md**: Comprehensive project examples
  - 6 simple projects (dog house, garden shed, deck, garage, outdoor kitchen, planters)
  - 2 medium complexity projects (pool house, workshop)
  - Tips for writing good project descriptions
  - Recommended projects by complexity level
  - Usage guide for dynamic planning
- **Updated README**:
  - Added link to EXAMPLE_PROJECTS.md
  - Added frontend linting commands to "Code Quality Tools" section
  - Organized by backend vs. frontend tools

**Files Created**: `docs/EXAMPLE_PROJECTS.md`
**Files Modified**: `README.md`

---

### 🔧 Minor Improvements

- Fixed auto-refresh indicator showing hardcoded "1 second" instead of actual config value
- Removed unused icon imports (Play, SkipForward)
- Improved error messages throughout
- Added console logging for debugging
- Better TypeScript error handling

---

## Session 3: Dynamic Planning Feature (Previous Session)

### 🧠 AI-Powered Dynamic Planning

- **Implemented dynamic planning system**: AI generates custom task breakdowns
- **Created project planner agent**: Uses Claude to analyze project descriptions
- **Added toggle in UI**: Optional for template projects, automatic for custom projects
- **Backend support**: `use_dynamic_planning` parameter in API
- **Task generation**: Intelligent task sequencing based on project requirements

**Files Created**: `backend/agents/project_planner.py`, `docs/DYNAMIC_PLANNING.md`
**Files Modified**: `backend/agents/general_contractor.py`, `backend/orchestration/task_manager.py`, `frontend/src/components/ProjectForm.tsx`, `backend/api/routes.py`

---

## Session 2: Core Fixes & Features

### 🔧 MCP Server Integration

- **Fixed MCP server connectivity**: Resolved stdio communication issues
- **Improved error handling**: Better MCP server failure recovery
- **Added MCP testing**: Integration tests for materials and permitting servers

**Files Modified**: `backend/mcp_servers/materials_supplier.py`, `backend/mcp_servers/permitting.py`, `tests/test_mcp_integration.py`

---

### 🗂️ Project Reorganization

- **Restructured directories**: Better separation of concerns
- **Organized agents**: Each agent in separate file
- **Improved imports**: Cleaner module structure
- **Better file naming**: More intuitive organization

**Files Affected**: Multiple (restructuring)

---

### 🔁 Loop Detection & Protection

- **Implemented loop detection**: Prevents agents from repeating same tool calls infinitely
- **Configurable thresholds**:
  - `MAX_CONSECUTIVE_TOOL_CALLS`
  - `MAX_TOTAL_TOOL_CALLS`
  - `MAX_IDENTICAL_CALLS`
- **Task timeout**: Prevents runaway execution
- **Recovery UI**: Skip/Retry buttons for failed tasks
- **Documentation**: Created LOOP_PROTECTION.md

**Files Created**: `backend/utils/loop_detection.py`, `docs/LOOP_PROTECTION.md`
**Files Modified**: Multiple agent files

---

### 🎯 Task Recovery System

- **Skip functionality**: Mark failed tasks as complete to unblock dependents
- **Retry functionality**: Reset and re-execute failed tasks
- **UI integration**: Red cards with action buttons
- **API endpoints**: `/api/tasks/{task_id}/skip` and `/api/tasks/{task_id}/retry`
- **Confirmation dialogs**: Prevent accidental actions

**Files Modified**: `backend/api/routes.py`, `frontend/src/components/DashboardSimple.tsx`

---

## Session 1: Initial Project Setup

### 🏗️ Core Architecture

- **FastAPI backend**: RESTful API with WebSocket support
- **React frontend**: TypeScript + Vite + Tailwind CSS
- **8 Specialized agents**: Architect, Carpenter, Electrician, Plumber, Mason, Painter, HVAC, Roofer
- **General Contractor orchestrator**: Central coordination agent
- **Task dependency system**: Automatic sequencing based on construction workflows
- **Phase-based execution**: 8 construction phases

---

### 🔌 MCP Servers

- **Materials Supplier Server**:
  - Tools: check_availability, order_materials, get_catalog, get_order
  - Categories: lumber, electrical, plumbing, masonry, paint, HVAC, roofing
- **Permitting Service Server**:
  - Tools: apply_for_permit, check_permit_status, schedule_inspection
  - Permit types: building, electrical, plumbing, mechanical, demolition, roofing

**Files Created**: `backend/mcp_servers/materials_supplier.py`, `backend/mcp_servers/permitting.py`

---

### 🎨 Frontend Dashboard

- **Real-time updates**: Live activity feed with auto-refresh
- **Stats cards**: Completion percentage, in progress, completed/total, failed
- **Phase progress bar**: Visual representation of 8 construction phases
- **Color-coded task cards**: Blue (active), red (failed), green (completed), yellow (queued)
- **Responsive design**: Works on desktop and mobile
- **Toast notifications**: User feedback for all actions

**Files Created**: `frontend/src/components/Dashboard.tsx`, `frontend/src/components/DashboardSimple.tsx`, `frontend/src/components/ProjectForm.tsx`, `frontend/src/components/AgentGraph.tsx`

---

### 🗄️ State Management

- **Zustand store**: Centralized project and task state
- **API client**: Axios-based client with type safety
- **WebSocket hook**: Real-time updates (for Dashboard.tsx)
- **Custom hooks**: Reusable logic for common patterns

**Files Created**: `frontend/src/store/projectStore.ts`, `frontend/src/api/client.ts`, `frontend/src/hooks/useWebSocket.ts`

---

### 📋 Project Templates

Pre-configured templates for common construction projects:

- Kitchen Remodel (10 tasks)
- Bathroom Remodel (11 tasks)
- Shed Construction (10 tasks)
- New Construction (14 tasks)
- Home Addition (11 tasks)
- Custom Projects (dynamic planning)

**Files Modified**: `backend/orchestration/task_manager.py`

---

### 📖 Initial Documentation

- **README.md**: Comprehensive project documentation
- **QUICKSTART.md**: Quick start guide
- **TESTING.md**: Testing documentation
- **EXECUTION_GUIDE.md**: Detailed execution instructions
- **SUMMARY.md**: Project overview
- **CURRENT_LIMITATIONS.md**: Known limitations

**Files Created**: Multiple documentation files in `docs/`

---

### 🧪 Testing Infrastructure

- **Demo mode**: Test without AWS (`test_shed_demo.py`)
- **Planning mode**: See task breakdown (`test_shed_detailed.py`)
- **Single agent test**: Verify AWS setup (`test_agent.py`)
- **Full execution mode**: Real Claude AI execution
- **MCP integration tests**: Test MCP servers

**Files Created**: `tests/test_shed_demo.py`, `tests/test_shed_detailed.py`, `tests/test_agent.py`, `tests/test_mcp_integration.py`

---

## Summary Statistics

### Across All Sessions

- **Total Commits**: 13+
- **Files Created**: 30+
- **Major Features**:
  - Multi-agent orchestration system
  - MCP server integration
  - Dynamic planning with AI
  - Loop detection & protection
  - Task recovery system
  - Backend health checks
  - Fully autonomous execution
- **Bug Fixes**: 20+
- **Documentation Pages**: 8
- **Lines of Code**: 10,000+
- **Code Quality Issues Fixed**: 19

### Key Transformations

- ❌ Manual execution → ✅ Fully autonomous
- ❌ Template-only → ✅ AI-powered dynamic planning
- ❌ Incomplete execution → ✅ Runs to 100% completion
- ❌ Hidden task states → ✅ Complete visibility (pending, blocked, etc.)
- ❌ Confusing UI → ✅ Clear, intuitive interface
- ❌ No health checks → ✅ Startup verification
- ❌ No code quality tools → ✅ ESLint configured
- ❌ Poor git hygiene → ✅ Clean repository (.env excluded, .gitignore proper)
- ❌ Hardcoded values → ✅ Configurable via environment

---

## Technology Stack

### Backend

- Python 3.13+
- Strands Agents framework
- AWS Bedrock (Claude Sonnet 4.5)
- FastAPI + Uvicorn
- Pydantic for validation
- MCP (Model Context Protocol) servers

### Frontend

- React 18
- TypeScript
- Vite (build tool)
- Tailwind CSS v3
- Zustand (state management)
- React Router
- Axios (API client)
- React Hot Toast (notifications)
- Lucide React (icons)
- ESLint (code quality)

---

## Breaking Changes

### Session 4 (Today)

- **Removed manual execution buttons**: System is now fully autonomous by default
- **Changed default refresh interval**: From 1s to 3s (configurable)
- **Navigation behavior**: Projects auto-navigate to dashboard on submission

### Session 3

- **Added dynamic planning**: New parameter in `/api/projects/start` endpoint

### Session 2

- **Project structure reorganization**: Import paths changed
- **Loop detection**: New configuration variables required

---

## Migration Guide

### Upgrading to Session 4 Changes

1. **Update environment files**:

   ```bash
   # Add to .env or frontend/.env
   VITE_UI_REFRESH_INTERVAL_MS=3000
   ```

2. **Run npm install** (if using ESLint):

   ```bash
   cd frontend && npm install
   ```

3. **No breaking API changes**: Backend API remains compatible

4. **UI Behavior Change**: Projects now execute automatically - users no longer need to click "Execute All"

---

## Known Issues & Future Enhancements

### Known Issues

- Some TypeScript strict mode warnings remain (acceptable)
- WebSocket reconnection logic has linting warnings (functional)
- MCP server call logging not visible in UI (planned for future)

### Planned Enhancements

- **MCP Activity Logging**: Show materials orders and permit applications in activity feed
- **Task detail view**: Click tasks to see full execution details
- **Export functionality**: Download project reports
- **Dark mode toggle**: User preference for theme
- **Project history**: Save and review past projects
- **Agent reasoning view**: See agent thought process in real-time

---

## Credits

Built with:

- [Strands Agents](https://strandsagents.com/latest/) framework
- Claude via AWS Bedrock
- Modern web technologies (React, TypeScript, FastAPI)
- Model Context Protocol (MCP) for tool integration

Designed to demonstrate multi-agent AI orchestration patterns in a real-world construction management scenario.
