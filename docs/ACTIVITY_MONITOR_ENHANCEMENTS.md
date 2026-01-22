# Activity Monitor Enhancements

## Summary

Enhanced the Activity Monitor UI to display comprehensive detailed information about agent activities by making events expandable to show their full `details` payload with rich metadata.

## What Was Added

### 1. Expandable Event Details ✨

Events that contain additional details now show expand/collapse arrows (▶/▼). Click any event to see:

- **Tool Calls**: Full argument values, argument count, and parameter names
- **Tool Results**: Complete return values, result type, size/length metadata
- **Agent Thinking**: Full reasoning text (no truncation), character count, truncation indicator
- **Task Details**: Complete descriptions, timestamps, result types
- **MCP Calls**: Service name, tool name, all arguments, and metadata
- **Error Details**: Full error messages, error length, failure timestamps

### 2. Enhanced Event Display

Each event now shows:

- ⏰ **Timestamp** - Precise time of event (HH:MM:SS format)
- 🏷️ **Event Type** - Color-coded prefix ([START], [TOOL], [THINK], etc.)
- 👤 **Agent Name** - Which agent performed the action
- 📋 **Task ID** - Associated task identifier (when applicable) - NEW!
- 💬 **Message** - Human-readable summary
- 📦 **Details** - Expandable JSON payload with full information and metadata

### 3. Rich Metadata in Details

#### Tool Calls

```json
{
  "tool": "frame_walls",
  "arguments": {
    "wall_height": 8,
    "wall_count": 4,
    "material": "2x4 lumber"
  },
  "arg_count": 3,
  "arg_keys": ["wall_height", "wall_count", "material"]
}
```

#### Tool Results

```json
{
  "tool": "frame_walls",
  "result": {
    "status": "success",
    "walls_framed": 4,
    "lumber_used": "48 pieces of 2x4x8"
  },
  "metadata": {
    "type": "dict",
    "keys": ["status", "walls_framed", "lumber_used"],
    "size": 3
  }
}
```

#### Agent Thinking (Full Text!)

```json
{
  "full_thinking": "I need to frame the walls before installing the roof. First, I'll measure and cut the studs to 8 feet. Then I'll assemble the wall frames on the ground and raise them into position. I'll need to ensure all walls are plumb and square before securing them. The 2x4 lumber should be sufficient for the wall framing...",
  "length": 1247,
  "truncated": true
}
```

#### Task Start

```json
{
  "description": "Frame walls for 10x12 shed with 8-foot height",
  "description_length": 48,
  "started_at": "2026-01-21T15:30:45.123456"
}
```

#### Task Complete

```json
{
  "result_summary": "Successfully framed 4 walls using 2x4 lumber. All walls are plumb and square.",
  "result_type": "str",
  "full_result": "Successfully framed 4 walls using 2x4 lumber. All walls are plumb and square. Used 48 pieces of 2x4x8 studs. Walls are ready for sheathing.",
  "completed_at": "2026-01-21T15:35:22.789012"
}
```

#### Task Failed

```json
{
  "error": "Tool 'frame_walls' failed: Insufficient lumber in inventory",
  "error_length": 58,
  "failed_at": "2026-01-21T15:32:10.456789"
}
```

#### MCP Calls

```json
{
  "service": "materials_supplier",
  "tool": "order_materials",
  "arguments": {
    "category": "lumber",
    "item": "2x4x8 studs",
    "quantity": 48
  },
  "arg_count": 3,
  "arg_keys": ["category", "item", "quantity"]
}
```

#### MCP Results

```json
{
  "service": "materials_supplier",
  "tool": "order_materials",
  "result": {
    "order_id": "ORD-12345",
    "status": "confirmed",
    "total_cost": 384.00,
    "delivery_date": "2026-01-22"
  },
  "metadata": {
    "type": "dict",
    "keys": ["order_id", "status", "total_cost", "delivery_date"],
    "size": 4
  }
}
```

### 4. Visual Improvements

- **Chevron Icons**: Clear visual indicator for expandable events (▶ collapsed, ▼ expanded)
- **Syntax Highlighting**: JSON details displayed in formatted, readable style
- **Dark Theme**: Details shown in darker panel with border for better contrast
- **Hover Effects**: Interactive feedback when hovering over expandable events
- **Task ID Display**: Purple-colored task IDs shown inline for easy tracking

## Backend Enhancements

### Enhanced Activity Logger

Updated `backend/utils/activity_logger.py` to capture richer metadata:

1. **Thinking Events**: Now include character count and truncation indicator
2. **Tool Calls**: Include argument count and parameter names
3. **Tool Results**: Include result type and size/length metadata
4. **Task Events**: Include timestamps for start/complete/failed
5. **MCP Events**: Include argument counts and result metadata

### Full Text Logging

Updated `backend/agents/general_contractor.py` to log complete reasoning:

- Removed 500-character truncation limit
- Removed 300-character truncation limit
- Now logs full agent reasoning text (truncation only happens in display, not storage)

## User Experience

### Before Enhancement

- Only saw truncated message text (500 chars max)
- No way to see full tool arguments or results
- Limited visibility into agent reasoning
- No metadata about data types or sizes
- Had to check backend logs for details

### After Enhancement

- Click any event to expand full details
- See complete tool arguments and return values
- Read FULL agent reasoning (no truncation!)
- See metadata about data types, sizes, counts
- See timestamps for task lifecycle events
- All information available in the UI
- No need to check backend logs for debugging

## Usage Tips

1. **Filter First**: Use the filter dropdown to narrow down to specific event types
2. **Expand Interesting Events**: Click events with arrows (▶/▼) to see full details
3. **Read Full Reasoning**: Expand [THINK] events to see complete agent thought process
4. **Track Tasks**: Look for Task IDs in purple to follow a specific task's lifecycle
5. **Debug Tool Calls**: Expand [TOOL] and [RESULT] events to see exact arguments and returns
6. **Copy Details**: Select and copy JSON from expanded details for debugging
7. **Pause Stream**: Pause the stream to carefully examine events without new ones scrolling in
8. **Export Logs**: Use Export button to save complete activity log

## Technical Implementation

### Frontend Changes (`frontend/src/components/ActivityMonitor.tsx`)

- Added `expandedEvents` state to track which events are expanded
- Added `ChevronDown` and `ChevronRight` icons from lucide-react
- Created `toggleExpand()` function to handle click events
- Created `formatDetails()` to pretty-print JSON
- Created `hasDetails()` to check if event has expandable content
- Enhanced event rendering with conditional expansion UI
- Added Task ID display in purple color

### Backend Changes

**`backend/utils/activity_logger.py`:**

- Enhanced `log_thinking()` - Added length and truncation metadata
- Enhanced `log_tool_call()` - Added arg_count and arg_keys
- Enhanced `log_tool_result()` - Added result type and size metadata
- Enhanced `log_task_start()` - Added started_at timestamp
- Enhanced `log_task_complete()` - Added result_type and completed_at
- Enhanced `log_task_failed()` - Added error_length and failed_at
- Enhanced `log_mcp_call()` - Added arg_count and arg_keys
- Enhanced `log_mcp_result()` - Added result metadata

**`backend/agents/general_contractor.py`:**

- Removed truncation from thinking logs (was 500 chars, now unlimited)
- Removed truncation from fallback thinking logs (was 300 chars, now unlimited)
- Removed truncation from planning thinking logs (was 500 chars, now unlimited)

## Example Scenarios

### Debugging Tool Failures

1. Filter to "Tool Calls"
2. Find the failed tool call
3. Expand to see exact arguments passed (with types and counts)
4. Expand the result to see error message and metadata

### Understanding Agent Reasoning

1. Filter to "Reasoning"
2. Expand thinking events
3. Read FULL reasoning chain (no truncation!)
4. Understand complete decision-making process

### Tracking Task Lifecycle

1. Look for Task IDs in purple
2. Filter events by clicking task ID (future enhancement)
3. See start time, completion time, and duration
4. View full results with type information

### Tracking MCP Service Usage

1. Filter to "MCP Calls"
2. Expand to see which services were called
3. View arguments with counts and keys
4. Verify correct data was sent/received with metadata

## Future Enhancements (Ideas)

- 🔍 **Search**: Search within event messages and details
- 🎨 **Syntax Highlighting**: Color-code JSON keys/values in details
- 📊 **Statistics**: Show counts of each event type
- 🔗 **Task Linking**: Click task ID to filter all events for that task
- 💾 **Bookmarks**: Mark important events for later review
- 📈 **Timeline View**: Visual timeline of agent activities
- 🔔 **Alerts**: Highlight errors and warnings more prominently
- ⏱️ **Duration Tracking**: Calculate and display task durations
- 📋 **Copy Button**: One-click copy of event details
- 🔄 **Diff View**: Compare tool arguments vs results side-by-side

## Files Modified

- ✅ `frontend/src/components/ActivityMonitor.tsx` - Enhanced with expandable details and Task ID display
- ✅ `backend/utils/activity_logger.py` - Added rich metadata to all event types
- ✅ `backend/agents/general_contractor.py` - Removed truncation limits for full text logging

## Testing Recommendations

1. **Start a Project**: Submit a project to generate activity
2. **Watch Events**: Observe events streaming in with Task IDs
3. **Expand Events**: Click events with arrows to see rich details
4. **Check Metadata**: Verify arg_count, result types, timestamps are present
5. **Read Full Thinking**: Expand thinking events and verify no truncation
6. **Test Filters**: Try different filter options
7. **Pause/Resume**: Test pausing and resuming the stream
8. **Export**: Export logs and verify format includes all metadata

## Date Completed

January 21, 2026
