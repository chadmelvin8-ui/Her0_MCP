# Quick Start Guide - UltimateMultiLangAgent

Get up and running with the agent in 5 minutes.

## 🚀 30-Second Setup

### Linux/macOS
```bash
cd UltimateMultiLangAgent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nano .env  # Add your API keys
python main.py --status
```

### Windows PowerShell
```powershell
cd UltimateMultiLangAgent
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
notepad .env  # Add your API keys
python main.py --status
```

---

## ⚙️ Configuration

Edit `.env` and choose ONE LLM provider:

### Option 1: OpenAI (Recommended for Production)
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo
```
**Get key:** https://platform.openai.com/api-keys

### Option 2: Anthropic Claude
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```
**Get key:** https://console.anthropic.com

### Option 3: Ollama (Local/Free - Recommended for Development)
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

**First, install and run Ollama:**
- Download from: https://ollama.ai
- Install and start the service
- Pull a model: `ollama pull mistral`

### Option 4: HuggingFace
```env
LLM_PROVIDER=huggingface
HUGGINGFACE_MODEL=meta-llama/Llama-2-7b-chat-hf
HUGGINGFACE_TOKEN=hf_your-token-here
```
**Get token:** https://huggingface.co/settings/tokens

---

## GitHub Setup (Optional but Recommended)

If you want to use GitHub features:

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `workflow`, `read:user`, `gist`
4. Copy the token and add to `.env`:
```env
GITHUB_TOKEN=ghp_your-token-here
GITHUB_USERNAME=your-github-username
```

---

## 🎯 First Task

```bash
python main.py --status
```

If you see ✓ green checkmarks, you're ready! Try:

```bash
python main.py --task "write a python script that prints hello world"
```

---

## 📚 More Commands

```bash
# Check status
python main.py --status

# Run a task
python main.py --task "your task here"

# Execute command
python main.py --command "python --version"

# Show help
python main.py --help
```

---

## ❌ Troubleshooting

**Issue:** `ModuleNotFoundError`
- **Solution:** Make sure your venv is activated: `source venv/bin/activate` (Linux/macOS) or `.\venv\Scripts\Activate.ps1` (Windows)

**Issue:** `OPENAI_API_KEY not set`
- **Solution:** Edit `.env` and add your API key for your chosen provider

**Issue:** Ollama connection refused
- **Solution:** Make sure Ollama is running: `ollama serve` (in another terminal)

**Issue:** Python version too old
- **Solution:** Install Python 3.9+: https://www.python.org/downloads/

---

## 🎓 Next Steps

1. **Read full docs:** See [README.md](./README.md)
2. **Check examples:** Visit `examples/` folder
3. **Explore tools:** Check `agent/tools/` for available capabilities
4. **Join community:** Add GitHub star ⭐

---

## 💡 Pro Tips

- **Local development?** Use Ollama (free, runs offline)
- **Production use?** Use OpenAI (most reliable)
- **Budget conscious?** Use HuggingFace or Anthropic
- **Learning?** Start with `--task` commands, then use Python API

---

**Questions?** Check the full [README.md](./README.md) or create an issue on GitHub!
