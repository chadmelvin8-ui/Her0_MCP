# MCP'Arsonist AI - Product Requirements Document

## Original Problem Statement
Build a complete AI-powered penetration testing terminal-based application called "MCP'Arsonist AI" with a companion web dashboard. The app integrates with Burp Suite via MCP (Model Context Protocol) and supports multiple AI backends (Ollama, OpenAI, Anthropic, Gemini).

## User Personas
1. **Security Researcher** - Needs automated vulnerability hunting with AI assistance
2. **Penetration Tester** - Requires session management and professional reporting
3. **Bug Bounty Hunter** - Wants quick vulnerability identification and evidence collection

## Core Requirements (Static)
- Multi-AI provider support (OpenAI, Anthropic, Gemini, Ollama)
- Session-based vulnerability hunting
- Interactive AI chat interface
- Proxy history analysis
- Vulnerability findings management
- Professional security reports
- Terminal-style dark theme UI

## What's Been Implemented (2026-03-28)
### Backend (FastAPI + MongoDB)
- [x] Session CRUD operations
- [x] Findings CRUD with severity filtering
- [x] AI chat integration (OpenAI, Anthropic, Gemini via Emergent LLM Key)
- [x] Ollama local model support
- [x] Proxy history management
- [x] Dashboard statistics API
- [x] Autonomous hunting mode (start/stop)
- [x] Report generation with JSON export
- [x] Configuration management
- [x] Mock data generation for testing

### Frontend (React + Shadcn UI)
- [x] Dashboard with real-time stats
- [x] Sessions management with Hunt/Stop controls
- [x] AI Chat with quick commands
- [x] Findings viewer with filtering
- [x] Proxy History viewer with request/response details
- [x] Settings page for AI provider configuration
- [x] Reports page with export functionality
- [x] Terminal-style dark theme (JetBrains Mono font, green accents)

## Prioritized Backlog

### P0 (MVP Complete)
- [x] Core session management
- [x] AI chat functionality
- [x] Basic vulnerability tracking

### P1 (Future)
- [ ] Real Burp Suite MCP integration
- [ ] CLI installer script (`pip install mcparsonist`)
- [ ] Curl-based installer (`curl | bash`)
- [ ] WebSocket real-time updates
- [ ] PDF report generation

### P2 (Nice to Have)
- [ ] Training mode for Burp Suite mastery
- [ ] Multi-step autonomous agent workflows
- [ ] Screenshot capture for findings
- [ ] Docker deployment option
- [ ] Team collaboration features

## Next Tasks
1. Implement real Burp Suite MCP server connection
2. Add CLI package distribution
3. Create installation scripts for cross-platform support
4. Add PDF export for reports
