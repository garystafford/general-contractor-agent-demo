# General Contractor AI - Frontend

React-based frontend for the General Contractor multi-agent construction management system.

## Features

- **Project Input Form** - Start new construction projects with templates or custom descriptions
- **Real-time Dashboard** - Monitor project progress with live updates via WebSocket
- **Agent Collaboration Graph** - Visualize agent and MCP server interactions in real-time
- **Task Board** - Kanban-style task management with status tracking
- **Phase Progress Tracking** - Visual representation of construction phases
- **Materials & Permits** - Integration with MCP servers for materials and permitting

## Tech Stack

- **React 18** with TypeScript
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **React Flow** - Graph visualization for agents
- **Zustand** - Lightweight state management
- **React Router** - Client-side routing
- **Axios** - HTTP client for API calls
- **React Hot Toast** - Toast notifications
- **Lucide React** - Icon library

## Prerequisites

- Node.js 18+ and npm
- Backend server running on `http://localhost:8000`

## Installation

```bash
cd frontend
npm install
```

## Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # API client for backend
│   ├── components/
│   │   ├── ProjectForm.tsx    # Project input form
│   │   ├── Dashboard.tsx      # Main dashboard with stats
│   │   ├── AgentGraph.tsx     # Agent visualization with React Flow
│   │   └── TaskBoard.tsx      # Kanban task board
│   ├── hooks/
│   │   └── useWebSocket.ts    # WebSocket connection hook
│   ├── store/
│   │   └── projectStore.ts    # Zustand global state
│   ├── types/
│   │   └── index.ts           # TypeScript type definitions
│   ├── App.tsx                # Main app with routing
│   ├── main.tsx               # Entry point
│   └── index.css              # Global styles with Tailwind
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## WebSocket Connections

The frontend connects to three WebSocket endpoints:

1. **`/ws/project-updates`** - Project status updates (every 2 seconds)
2. **`/ws/task-updates`** - Individual task status changes (every 1 second)
3. **`/ws/agent-activity`** - Agent activity for visualization (every 0.5 seconds)

All WebSocket connections include automatic reconnection logic.

## API Endpoints Used

- `POST /api/projects/start` - Start new project
- `POST /api/projects/execute-next-phase` - Execute next phase
- `POST /api/projects/execute-all` - Execute entire project
- `GET /api/projects/status` - Get project status
- `POST /api/projects/reset` - Reset project
- `GET /api/tasks` - Get all tasks
- `GET /api/agents` - Get available agents

## Environment Variables

Create a `.env` file if you need to customize the API URL:

```env
VITE_API_URL=http://localhost:8000
```

## Features Overview

### 1. Project Form
- Select from predefined templates (Kitchen, Bathroom, etc.) or custom projects
- Option to use AI-powered dynamic planning
- Detailed project description input

### 2. Dashboard
- Real-time project statistics (completion %, tasks in progress, etc.)
- Construction phase progress bar
- Agent collaboration graph showing active agents and MCP servers
- Execute controls (Next Phase, Execute All, Reset)

### 3. Agent Graph
- Visual representation of all agents and MCP servers
- Nodes light up when agents are active
- Animated edges show task delegation
- Real-time updates via WebSocket

### 4. Task Board
- Kanban board with columns: Pending, Ready, In Progress, Completed, Failed
- Task cards showing agent, description, phase, and dependencies
- Real-time task status updates
- Task summary statistics

## Troubleshooting

### WebSocket Connection Issues

If WebSocket connections fail:
1. Ensure backend is running on `http://localhost:8000`
2. Check browser console for connection errors
3. WebSocket connections will auto-reconnect (max 5 attempts)

### CORS Issues

If you see CORS errors:
1. Backend CORS is configured to allow all origins
2. Check that backend is running and accessible
3. Verify API URL in the API client (`src/api/client.ts`)

### Build Errors

If you encounter TypeScript errors:
```bash
npm run build -- --mode development
```

## Development Tips

- Use browser DevTools to inspect WebSocket messages
- Redux DevTools compatible with Zustand store
- Hot Module Replacement (HMR) is enabled for fast development
- Tailwind CSS IntelliSense extension recommended for VS Code

## License

This project is part of the General Contractor Agent Demo.
