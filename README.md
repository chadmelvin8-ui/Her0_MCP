# Her0_MCP - Elite Security & AI Agent Platform

A comprehensive platform combining an autonomous multi-language coding agent with advanced security testing and penetration testing capabilities via Burp Suite MCP integration.

![Version](https://img.shields.io/badge/version-2.0.0-orange)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue)
![Status](https://img.shields.io/badge/status-active-brightgreen)

---

## 📦 Project Structure

```
Her0_MCP/
├── UltimateMultiLangAgent/     # 🤖 Autonomous coding agent
│   ├── agent/                  # Agent core logic
│   ├── config/                 # Configuration management
│   ├── examples/               # Usage examples
│   ├── main.py                 # Agent CLI entry point
│   └── requirements.txt         # Python dependencies
│
├── backend/                    # 🔌 FastAPI backend server
│   ├── server.py               # Main FastAPI app
│   ├── mcp_client.py           # Burp Suite MCP client
│   ├── autonomous_hunter.py    # Security automation
│   └── requirements.txt         # Backend dependencies
│
├── frontend/                   # 🎨 React web interface
│   ├── src/                    # React components
│   ├── components/             # UI components
│   ├── pages/                  # Page views
│   └── package.json            # Node.js dependencies
│
├── QUICKSTART.md               # ⚡ Quick start guide
└── memory/                     # 📝 Project documentation
```

---

## 🚀 Core Components

### 1. **UltimateMultiLangAgent** 🤖
Elite autonomous coding agent that can:
- Write and execute code in **50+ programming languages**
- Perform file operations with full filesystem access
- Execute terminal commands with safety guards
- Manage GitHub repositories (create, clone, push)
- Self-improve and extend its own capabilities
- Support multiple LLM providers (OpenAI, Anthropic, Ollama, HuggingFace)

**Quick Start:**
```bash
cd UltimateMultiLangAgent
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
python main.py --status
```

[👉 Full Agent Documentation](./UltimateMultiLangAgent/README.md)

### 2. **FastAPI Backend** 🔌
RESTful API server with:
- Burp Suite MCP integration for security testing
- WebSocket support for real-time updates
- MongoDB data persistence
- Security finding storage and analysis
- Proxy interception and modification capabilities

**Start Backend:**
```bash
cd backend
pip install -r requirements.txt
python server.py
# Runs on http://localhost:8000
```

### 3. **React Frontend** 🎨
Modern web interface featuring:
- Real-time security monitoring dashboard
- Interceptor for HTTP request/response modification
- Finding management and reporting
- Session management
- Integration with Burp Suite

**Start Frontend:**
```bash
cd frontend
npm install
npm start
# Runs on http://localhost:3000
```

---

## ⚡ Quick Start (5 minutes)

### Prerequisites
- Python 3.9+
- Node.js 16+ (for frontend)
- Git
- (Optional) Ollama for local LLM

### Step 1: Clone & Setup Agent
```bash
cd UltimateMultiLangAgent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Configure LLM Provider
```bash
# Edit .env - choose ONE provider:
nano .env
```

Choose your LLM:
- **Ollama** (Free, local) - Recommended for development
- **OpenAI** (Reliable) - Recommended for production
- **Anthropic Claude** (Powerful)
- **HuggingFace** (Budget-friendly)

### Step 3: Test Agent
```bash
python main.py --status
```

### Step 4: Run Your First Task
```bash
python main.py --task "write a hello world script in python and javascript"
```

---

## 📋 Configuration

### Agent LLM Providers

**`.env` Configuration:**
```env
# Option 1: Ollama (Recommended for development)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Option 2: OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo

# Option 3: Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Option 4: HuggingFace
LLM_PROVIDER=huggingface
HUGGINGFACE_MODEL=meta-llama/Llama-2-7b-chat-hf
HUGGINGFACE_TOKEN=hf_your-token-here

# GitHub (Optional)
GITHUB_TOKEN=ghp_your-token-here
GITHUB_USERNAME=your-github-username
```

### Setup Ollama (Free Local LLM)
```bash
# Download from https://ollama.ai
# Install and run:
ollama serve

# In another terminal, pull a model:
ollama pull mistral  # or: llama2, neural-chat, etc.
```

---

## 🎯 Usage Examples

### Agent - Command Line
```bash
# Check status
python main.py --status

# Execute a task
python main.py --task "Create a REST API in Node.js with Express"

# Run shell command
python main.py --command "npm --version"

# Create GitHub repo
python main.py --create-repo my-project "My awesome project"
```

### Agent - Python API
```python
from agent.core import UltimateMultiLangAgent

agent = UltimateMultiLangAgent()

# Execute task
result = agent.execute_task("Write a Python web scraper for news sites")

# Write code
agent.write_code("python", "print('Hello')", "app.py")

# Run code
output = agent.run_code("python", "print('From agent')")

# Execute command
result = agent.execute_command("ls -la")

# Get status
status = agent.get_status()
```

### Full Stack Setup
```bash
# Terminal 1: Backend
cd backend
python server.py

# Terminal 2: Frontend
cd frontend
npm start

# Terminal 3: Agent (optional)
cd UltimateMultiLangAgent
python main.py --task "your task here"
```

---

## 🛠️ Supported Languages

**Agent can write and execute code in:**
Python, JavaScript/TypeScript, Java, C, C++, Rust, Go, PHP, Ruby, C#, Kotlin, Swift, Solidity, Bash, Perl, R, MATLAB, Lua, Haskell, Scala, Clojure, Groovy, Ruby, Objective-C, VB.NET, F#, Dart, Elixir, Erlang, and 20+ more.

---

## 📊 Features

### Agent Features
- ✨ Multi-language code generation
- 💾 Full filesystem access
- 🖥️ Terminal command execution
- 🔗 GitHub integration
- 🧠 Self-improvement capabilities
- 📝 Documentation generation
- 🐛 Code debugging
- 🔍 Code analysis

### Backend Features
- 🔌 Burp Suite MCP integration
- 📝 Security finding storage
- 🔄 Real-time WebSocket updates
- 🛡️ Request/response interception
- 📊 Vulnerability tracking
- 🗄️ MongoDB persistence

### Frontend Features
- 📊 Dashboard with real-time metrics
- 🔍 Request/response interceptor
- 📝 Finding management system
- 📈 Security reports
- 🎯 Session tracking
- ⚙️ System settings

---

## ⚙️ Installation & Setup

### Linux/macOS
```bash
# Agent setup
cd UltimateMultiLangAgent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Backend setup
cd ../backend
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### Windows PowerShell
```powershell
# Agent setup
cd UltimateMultiLangAgent
python -m venv venv
.\venv\Scripts\Activate.ps1
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
pip install -r requirements.txt

# Backend setup
cd ..\backend
pip install -r requirements.txt

# Frontend setup
cd ..\frontend
npm install
```

---

## 🌐 API Endpoints

### Health Check
```
GET /health
```

### Security Findings
```
GET /api/findings              # List all findings
POST /api/findings             # Create finding
GET /api/findings/{id}         # Get specific finding
PUT /api/findings/{id}         # Update finding
DELETE /api/findings/{id}      # Delete finding
```

### Sessions
```
GET /api/sessions              # List sessions
POST /api/sessions             # Create session
GET /api/sessions/{id}         # Get session details
```

### Interceptor
```
POST /api/intercept            # Intercept request
PUT /api/intercept/{id}        # Modify request/response
```

---

## 🔒 Security & Safety

- **Command Whitelisting:** Only approved commands can be executed
- **API Key Protection:** Never commit keys to version control
- **Timeout Guards:** All operations have timeouts to prevent hangs
- **Destructive Commands:** Can be disabled via `ENABLE_DESTRUCTIVE_COMMANDS=false`
- **Filesystem Boundaries:** Operations confined to workspace directory

---

## 📖 Documentation

- [Quick Start Guide](./QUICKSTART.md) - Get running in 5 minutes
- [Agent Documentation](./UltimateMultiLangAgent/README.md) - Full agent capabilities
- [Backend Docs](./backend/README.md) - API and server details
- [Design Guidelines](./design_guidelines.json) - UI/UX standards
- [Project Roadmap](./memory/PRD.md) - Future plans

---

## 🤝 Contributing

Contributions welcome! Areas:
- Additional language support
- New security testing modules
- Frontend UI improvements
- Documentation expansions
- Bug fixes and optimizations

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🆘 Troubleshooting

**Agent won't start?**
- Check Python version: `python --version` (need 3.9+)
- Verify venv: `source venv/bin/activate`
- Check .env file exists and has correct keys

**Backend connection refused?**
- Ensure backend is running: `python server.py`
- Check MongoDB connection string in .env

**Frontend won't connect?**
- Backend must be running on http://localhost:8000
- Check CORS settings if getting 403 errors

**Ollama not working?**
- Ensure Ollama is running: `ollama serve`
- Check URL: `curl http://localhost:11434/api/tags`

---

## 📞 Support

- 📧 Create an issue on GitHub
- 💬 Check discussions section
- 📚 Read full documentation in `memory/` folder
- 🤖 Ask the agent: `python main.py --task "help me with..."`

---

**Ready to start?** → [Quick Start Guide](./QUICKSTART.md)

