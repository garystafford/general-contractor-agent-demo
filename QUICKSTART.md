# Quick Start Guide

## 🎯 Run the Demo NOW (No AWS Required!)

The easiest way to see the detailed agent output:

```bash
uv run test_shed_demo.py
```

This shows **simulated agent reasoning and tool calling** that looks exactly like what the real execution will show!

---

## 📊 Available Test Scripts

### 1. **Demo Mode** ⭐ RECOMMENDED FIRST
```bash
uv run test_shed_demo.py
```
- ✅ No AWS required
- Shows detailed agent reasoning
- Shows tool calls with inputs/outputs
- Simulated but realistic output
- **Run this first to see what to expect!**

### 2. **Planning Mode**
```bash
uv run test_shed_detailed.py
```
- ✅ No AWS required
- Shows complete task breakdown
- Shows dependencies and phases
- Good for understanding the project structure

### 3. **Real AI Execution** 🤖
```bash
uv run test_shed_detailed.py execute
```
- ⚠️ Requires valid AWS Bedrock credentials
- ⚠️ Requires correct model ID in `.env`
- Real Claude AI agents execute tasks
- Live streaming of agent reasoning
- **Only run this after configuring AWS!**

---

## 🔧 AWS Configuration (For Real Execution Only)

### Step 1: Get Your Model ID

1. Go to AWS Bedrock Console
2. Navigate to "Model access"
3. Find the exact model ID for Claude
4. Common formats:
   - `us.anthropic.claude-sonnet-4-5-v1:0`
   - `anthropic.claude-sonnet-4-5-20250929-v1:0`

### Step 2: Update .env

Edit `.env`:
```bash
# Uncomment and fill in your credentials
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_SESSION_TOKEN=your_token_here  # If using temporary credentials

# Or use AWS profile
AWS_PROFILE=default

# Update with YOUR model ID from Step 1
DEFAULT_MODEL=us.anthropic.claude-sonnet-4-5-v1:0
```

### Step 3: Test Single Agent First

Before running the full project:
```bash
uv run test_agent.py
```

If this works, you're ready for the full execution!

---

## 📖 What Each Script Does

| Script | AWS Required? | Shows Agent Reasoning? | Duration |
|--------|---------------|------------------------|----------|
| `test_shed_demo.py` | ❌ No | ✅ Yes (simulated) | 30 sec |
| `test_shed_detailed.py` | ❌ No | ❌ No | < 1 sec |
| `test_shed_detailed.py execute` | ✅ Yes | ✅ Yes (REAL AI!) | 5-10 min |
| `test_agent.py` | ✅ Yes | ✅ Yes | 30 sec |

---

## 🎬 Expected Output

### Demo Mode Output:
```
┌──────────────────────────────────────────────────────┐
│ TASK #3: Frame walls and install door/window openings
│ Agent: Carpenter
│ Phase: FRAMING
└──────────────────────────────────────────────────────┘

💭 I'll frame all four walls with proper openings...
💭 Using 2x4 lumber at 16-inch centers...

🔧 Calling tool: frame_walls
   Input: {
      "wall_count": 4,
      "wall_length": 10.0,
      "stud_spacing": 16
   }
✓ Tool completed successfully
   Result: {
      "status": "success",
      "details": "Framed 4 walls..."
   }
```

---

## ❓ Common Questions

**Q: Do I need AWS to see the demo?**
A: No! Run `test_shed_demo.py` to see everything without AWS.

**Q: What's the difference between demo and execution?**
A: Demo shows simulated output. Execution uses real Claude AI.

**Q: How much does execution cost?**
A: Approximately $0.10-0.50 for the full 10-task project.

**Q: Can I run just one task?**
A: Yes, use `test_agent.py` to test a single agent.

**Q: What if I get "model identifier is invalid"?**
A: Update `DEFAULT_MODEL` in `.env` with the correct ID from AWS Console.

---

## 🚀 Next Steps

1. **Run the demo** → `uv run test_shed_demo.py`
2. **See the project plan** → `uv run test_shed_detailed.py`
3. **Configure AWS** → Edit `.env` with your credentials
4. **Test single agent** → `uv run test_agent.py`
5. **Run full execution** → `uv run test_shed_detailed.py execute`

---

## 📚 More Information

- **[TESTING.md](TESTING.md)** - Complete testing documentation
- **[EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)** - Detailed execution mode guide
- **[README.md](README.md)** - Full project documentation

---

## 💡 Pro Tips

- Start with demo mode to understand the flow
- Demo shows exactly what real execution looks like
- Test with single agent before full project
- Watch for the real-time streaming in execution mode
- Each task takes 30-60 seconds with real AI
- Full project takes 5-10 minutes with AWS
