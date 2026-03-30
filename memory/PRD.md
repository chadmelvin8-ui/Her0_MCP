# MCP'Arsonist AI - Product Requirements Document

## Original Problem Statement
Build a complete, REAL working AI-powered penetration testing application called "MCP'Arsonist AI" with:
- Real Burp Suite MCP integration (not simulation)
- Proxy interceptor for capturing/modifying requests
- Import functionality for Burp exports (.xml, .json)
- Autonomous hunting with active testing capabilities
- Multi-AI provider support (OpenAI, Anthropic, Gemini, Ollama)
- Full authorization flow for active testing modes

## User Personas
1. **Security Researcher** - Uses passive analysis for safe vulnerability discovery
2. **Penetration Tester** - Requires active testing with full tool integration
3. **Bug Bounty Hunter** - Needs efficient autonomous hunting with evidence collection

## Core Requirements (Static)
- Real MCP protocol connection to Burp Suite
- Proxy interception with Forward/Drop/Modify capabilities
- Multiple hunting strategies (passive, active_safe, active_full)
- Import Burp exports for offline analysis
- AI-powered vulnerability analysis
- Professional security reports

## What's Been Implemented (2026-03-30)

### Backend (FastAPI + MongoDB)
- [x] Real BurpMCPClient with full MCP protocol support
- [x] All MCP tools: proxy_history, send_request, repeater, intruder, scope, site_map
- [x] ProxyInterceptor class with request capture/modification
- [x] Match & Replace rules engine
- [x] Request/Response modifiers (add/remove headers, change method, inject scripts)
- [x] AutonomousHunter with pattern-based detection
- [x] Hunting strategies: PASSIVE, ACTIVE_SAFE, ACTIVE_FULL
- [x] BurpExportParser for XML and JSON imports
- [x] WebSocket support for real-time updates
- [x] AI integration via Emergent LLM Key
- [x] File upload for Burp exports

### Frontend (React + Shadcn UI)
- [x] Dashboard with Burp connection status
- [x] Sessions with Import/Hunt dialogs
- [x] Hunt authorization flow (3 modes)
- [x] Interceptor page with request editor
- [x] Forward/Drop/Forward Modified actions
- [x] Send to Repeater/Intruder buttons
- [x] AI Chat with auto-context fetching
- [x] Findings management with severity filtering
- [x] Proxy History viewer
- [x] Settings for AI provider configuration
- [x] Professional report generation

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Web Browser   │────▶│  React Frontend  │────▶│  FastAPI Backend│
│    (User)       │     │  (Dashboard UI)  │     │   (Port 8001)   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          │ MCP Protocol
                                                          │ (HTTP/SSE)
                                                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Burp Suite (User's Machine)                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │  Proxy (8080)   │  │    Repeater     │  │    Intruder     │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
│                          MCP Server Extension (Port 9876)            │
└─────────────────────────────────────────────────────────────────────┘
```

## Prioritized Backlog

### P0 (MVP Complete) ✅
- [x] Real MCP client implementation
- [x] Interceptor with Forward/Drop
- [x] Autonomous hunting (passive + active)
- [x] File import for Burp exports
- [x] AI analysis integration

### P1 (Next Phase)
- [ ] CLI installer script (`pip install mcparsonist`)
- [ ] Real-time SSE streaming from Burp
- [ ] PDF report export
- [ ] Custom vulnerability signatures

### P2 (Future)
- [ ] Docker deployment option
- [ ] Training mode for Burp Suite mastery
- [ ] Team collaboration features
- [ ] Vulnerability database integration

## Setup Instructions for Users

1. Install Burp Suite Community/Pro Edition
2. Clone and build MCP Server: https://github.com/PortSwigger/mcp-server
3. Load MCP Server JAR as Burp extension
4. MCP Server runs on 127.0.0.1:9876
5. Access MCP'Arsonist AI web dashboard
6. Create session and start hunting!

## Next Tasks
1. Create pip-installable CLI package
2. Add PDF export for reports
3. Implement custom signature editor
4. Add rate limiting for active tests
