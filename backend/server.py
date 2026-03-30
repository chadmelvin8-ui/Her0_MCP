from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json
import asyncio
from enum import Enum

# Import real MCP modules
from mcp_client import BurpMCPClient, BurpExportParser
from autonomous_hunter import AutonomousHunter, HuntingStrategy, Finding
from interceptor import ProxyInterceptor, RequestModifier, ResponseModifier

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="MCP'Arsonist AI", version="2.0.0")

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===================== GLOBAL INSTANCES =====================
# MCP Client for Burp Suite connection
mcp_client = BurpMCPClient()
# Proxy Interceptor
interceptor = ProxyInterceptor(mcp_client)
# Active WebSocket connections for real-time updates
ws_connections: List[WebSocket] = []

# ===================== ENUMS =====================
class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"

class SessionStatus(str, Enum):
    IDLE = "idle"
    HUNTING = "hunting"
    ANALYZING = "analyzing"
    COMPLETED = "completed"

# ===================== MODELS =====================
class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ai_provider: AIProvider = AIProvider.OPENAI
    ai_model: str = "gpt-5.2"
    burp_host: str = "127.0.0.1"
    burp_port: int = 9876
    ollama_url: str = "http://localhost:11434"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConfigUpdate(BaseModel):
    ai_provider: Optional[AIProvider] = None
    ai_model: Optional[str] = None
    burp_host: Optional[str] = None
    burp_port: Optional[int] = None
    ollama_url: Optional[str] = None

class SessionModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    target_url: Optional[str] = None
    status: SessionStatus = SessionStatus.IDLE
    findings_count: int = 0
    requests_analyzed: int = 0
    burp_connected: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionCreate(BaseModel):
    name: str
    target_url: Optional[str] = None

class FindingModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    title: str
    description: str
    severity: SeverityLevel
    vulnerability_type: str
    confidence: str = "tentative"
    evidence: str
    request_data: Optional[str] = None
    response_data: Optional[str] = None
    recommendations: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FindingCreate(BaseModel):
    session_id: str
    title: str
    description: str
    severity: SeverityLevel
    vulnerability_type: str
    confidence: str = "tentative"
    evidence: str
    request_data: Optional[str] = None
    response_data: Optional[str] = None
    recommendations: List[str] = []

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str
    content: str
    tool_calls: Optional[List[Dict]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatMessageCreate(BaseModel):
    session_id: str
    content: str

class ProxyHistoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    method: str
    url: str
    host: str
    path: str
    status_code: Optional[int] = None
    request_headers: Dict[str, str] = {}
    request_body: Optional[str] = None
    response_headers: Dict[str, str] = {}
    response_body: Optional[str] = None
    raw_request: Optional[str] = None
    raw_response: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    analyzed: bool = False
    flags: List[str] = []

class HuntRequest(BaseModel):
    strategy: str = "passive"  # passive, active_safe, active_full
    authorized: bool = False
    target_scope: List[str] = []

class InterceptActionRequest(BaseModel):
    action: str  # forward, drop, forward_modified
    modified_content: Optional[str] = None

class MatchReplaceRule(BaseModel):
    match_type: str  # request_header, request_body, response_header, response_body
    match_pattern: str
    replace_with: str
    enabled: bool = True

class MCPToolCallRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}

class DashboardStats(BaseModel):
    total_sessions: int = 0
    active_sessions: int = 0
    total_findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    info_findings: int = 0
    requests_analyzed: int = 0
    burp_connected: bool = False
    intercept_enabled: bool = False
    recent_findings: List[Dict[str, Any]] = []

# ===================== AI SERVICE =====================
class AIService:
    def __init__(self):
        self.system_prompt = """You are MCP'Arsonist AI, an elite autonomous penetration testing assistant integrated with Burp Suite via MCP (Model Context Protocol).

You have REAL access to Burp Suite tools through MCP. You can:
1. Fetch and analyze proxy history
2. Send HTTP requests via Repeater
3. Prepare payloads for Intruder
4. Check and modify scope
5. Search for patterns in traffic
6. Create findings in Burp

When analyzing traffic, be thorough:
- Look for IDOR (sequential IDs, UUIDs that might be guessable)
- Check for XSS (reflected input, missing CSP)
- Identify SQLi (error messages, timing)
- Find authentication flaws (weak tokens, missing auth)
- Spot logic bugs (race conditions, state manipulation)
- Detect sensitive data exposure

For ACTIVE testing (when authorized):
- Test parameter manipulation
- Verify access controls
- Probe injection points
- Test business logic

Always provide:
- Clear reasoning for each step
- Evidence from actual requests/responses
- Severity assessment
- Actionable remediation advice

Format findings clearly with [SEVERITY] tags."""

    async def get_ai_response(self, messages: List[Dict], config: Dict) -> str:
        provider = config.get('ai_provider', 'openai')
        model = config.get('ai_model', 'gpt-5.2')
        
        if provider == 'ollama':
            return await self._ollama_chat(messages, model, config.get('ollama_url', 'http://localhost:11434'))
        else:
            return await self._emergent_chat(messages, provider, model)
    
    async def _emergent_chat(self, messages: List[Dict], provider: str, model: str) -> str:
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            api_key = os.environ.get('EMERGENT_LLM_KEY', '')
            if not api_key:
                return "[ERROR] EMERGENT_LLM_KEY not configured. Please set your API key in settings."
            
            chat = LlmChat(
                api_key=api_key,
                session_id=str(uuid.uuid4()),
                system_message=self.system_prompt
            )
            
            if provider == 'anthropic':
                chat.with_model("anthropic", model if model else "claude-sonnet-4-5-20250929")
            elif provider == 'gemini':
                chat.with_model("gemini", model if model else "gemini-3-flash-preview")
            else:
                chat.with_model("openai", model if model else "gpt-5.2")
            
            user_content = messages[-1]['content'] if messages else "Hello"
            user_message = UserMessage(text=user_content)
            
            response = await chat.send_message(user_message)
            return response
        except Exception as e:
            logger.error(f"AI chat error: {e}")
            return f"[ERROR] AI request failed: {str(e)}"
    
    async def _ollama_chat(self, messages: List[Dict], model: str, ollama_url: str) -> str:
        import aiohttp
        try:
            formatted_messages = [{"role": "system", "content": self.system_prompt}]
            formatted_messages.extend(messages)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ollama_url}/api/chat",
                    json={"model": model, "messages": formatted_messages, "stream": False},
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('message', {}).get('content', '[No response]')
                    else:
                        return f"[ERROR] Ollama returned status {resp.status}"
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"[ERROR] Ollama connection failed: {str(e)}"

ai_service = AIService()

# ===================== HELPER FUNCTIONS =====================
async def get_config() -> dict:
    config = await db.config.find_one({}, {"_id": 0})
    if not config:
        default_config = ConfigModel().model_dump()
        default_config['created_at'] = default_config['created_at'].isoformat()
        default_config['updated_at'] = default_config['updated_at'].isoformat()
        insert_doc = dict(default_config)
        await db.config.insert_one(insert_doc)
        return default_config
    return config

async def broadcast_ws(event_type: str, data: Dict):
    """Broadcast message to all WebSocket connections"""
    message = json.dumps({"type": event_type, "data": data})
    for ws in ws_connections[:]:
        try:
            await ws.send_text(message)
        except:
            ws_connections.remove(ws)

async def update_mcp_client():
    """Update MCP client with current config"""
    config = await get_config()
    mcp_client.host = config.get('burp_host', '127.0.0.1')
    mcp_client.port = config.get('burp_port', 9876)
    mcp_client.base_url = f"http://{mcp_client.host}:{mcp_client.port}"

# ===================== ROUTES =====================

@api_router.get("/")
async def root():
    return {"message": "MCP'Arsonist AI API v2.0", "status": "operational"}

@api_router.get("/health")
async def health_check():
    # Check Burp connection
    await update_mcp_client()
    status = await mcp_client.get_status()
    return {
        "status": "healthy",
        "service": "MCP'Arsonist AI",
        "burp_connected": status.success,
        "burp_status": status.data if status.success else status.error
    }

# ===================== CONFIG ROUTES =====================
@api_router.get("/config")
async def get_configuration():
    return await get_config()

@api_router.put("/config")
async def update_configuration(update: ConfigUpdate):
    config = await get_config()
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.config.update_one({"id": config['id']}, {"$set": update_data})
    
    # Update MCP client
    await update_mcp_client()
    
    updated = await db.config.find_one({"id": config['id']}, {"_id": 0})
    return updated

# ===================== BURP MCP CONNECTION =====================
@api_router.get("/burp/status")
async def get_burp_status():
    """Get Burp Suite MCP connection status"""
    await update_mcp_client()
    result = await mcp_client.get_status()
    return {
        "connected": result.success,
        "data": result.data if result.success else None,
        "error": result.error if not result.success else None
    }

@api_router.post("/burp/connect")
async def connect_to_burp():
    """Connect to Burp Suite MCP Server"""
    await update_mcp_client()
    connected = await mcp_client.connect()
    return {"connected": connected}

@api_router.post("/burp/tool")
async def call_burp_tool(request: MCPToolCallRequest):
    """Call any Burp MCP tool directly"""
    await update_mcp_client()
    result = await mcp_client.call_tool(request.tool_name, request.parameters)
    return {
        "success": result.success,
        "data": result.data,
        "error": result.error
    }

@api_router.get("/burp/proxy-history")
async def get_burp_proxy_history(limit: int = 100, regex: Optional[str] = None):
    """Get proxy history directly from Burp"""
    await update_mcp_client()
    if regex:
        result = await mcp_client.get_proxy_history_filtered(regex, limit)
    else:
        result = await mcp_client.get_proxy_history(limit)
    return {
        "success": result.success,
        "items": result.data if result.success else [],
        "error": result.error if not result.success else None
    }

@api_router.post("/burp/send-request")
async def send_request_via_burp(request: str, host: str, port: int = 443, https: bool = True):
    """Send HTTP request through Burp"""
    await update_mcp_client()
    result = await mcp_client.send_http_request(request, host, port, https)
    return {
        "success": result.success,
        "response": result.data if result.success else None,
        "error": result.error if not result.success else None
    }

@api_router.post("/burp/repeater")
async def create_repeater_tab(request: str, host: str, port: int = 443, 
                              https: bool = True, tab_name: str = "MCP"):
    """Create a new Repeater tab in Burp"""
    await update_mcp_client()
    result = await mcp_client.create_repeater_tab(request, host, port, https, tab_name)
    return {"success": result.success, "error": result.error if not result.success else None}

@api_router.post("/burp/intruder")
async def send_to_intruder(request: str, host: str, port: int = 443, https: bool = True):
    """Send request to Intruder in Burp"""
    await update_mcp_client()
    result = await mcp_client.send_to_intruder(request, host, port, https)
    return {"success": result.success, "error": result.error if not result.success else None}

@api_router.get("/burp/site-map")
async def get_site_map(limit: int = 100, regex: Optional[str] = None):
    """Get site map from Burp"""
    await update_mcp_client()
    if regex:
        result = await mcp_client.get_site_map_filtered(regex, limit)
    else:
        result = await mcp_client.get_site_map(limit)
    return {
        "success": result.success,
        "items": result.data if result.success else [],
        "error": result.error if not result.success else None
    }

@api_router.post("/burp/scope/check")
async def check_scope(url: str):
    """Check if URL is in Burp scope"""
    await update_mcp_client()
    result = await mcp_client.check_scope(url)
    return {"in_scope": result.data if result.success else False, "error": result.error}

@api_router.post("/burp/scope/include")
async def include_in_scope(url: str):
    """Add URL to Burp scope"""
    await update_mcp_client()
    result = await mcp_client.include_in_scope(url)
    return {"success": result.success, "error": result.error if not result.success else None}

# ===================== INTERCEPTOR ROUTES =====================
@api_router.get("/interceptor/status")
async def get_interceptor_status():
    """Get interceptor status"""
    return await interceptor.get_status()

@api_router.post("/interceptor/toggle")
async def toggle_interceptor():
    """Toggle proxy interception"""
    success = await interceptor.toggle_intercept()
    status = await interceptor.get_status()
    await broadcast_ws("intercept_status", status)
    return status

@api_router.post("/interceptor/enable")
async def enable_interceptor():
    """Enable proxy interception"""
    success = await interceptor.enable_intercept()
    return {"success": success, "enabled": interceptor.intercept_enabled}

@api_router.post("/interceptor/disable")
async def disable_interceptor():
    """Disable proxy interception"""
    success = await interceptor.disable_intercept()
    return {"success": success, "enabled": interceptor.intercept_enabled}

@api_router.get("/interceptor/requests")
async def get_intercepted_requests():
    """Get pending intercepted requests"""
    requests = interceptor.get_pending_requests()
    return [{"id": r.id, "method": r.method, "url": r.url, "host": r.host,
             "raw_request": r.raw_request, "intercepted_at": r.intercepted_at} for r in requests]

@api_router.get("/interceptor/responses")
async def get_intercepted_responses():
    """Get pending intercepted responses"""
    responses = interceptor.get_pending_responses()
    return [{"id": r.id, "status_code": r.status_code, "raw_response": r.raw_response,
             "intercepted_at": r.intercepted_at} for r in responses]

@api_router.post("/interceptor/request/{request_id}/forward")
async def forward_request(request_id: str, action: InterceptActionRequest):
    """Forward or drop an intercepted request"""
    if action.action == "forward":
        success = await interceptor.forward_request(request_id)
    elif action.action == "forward_modified":
        success = await interceptor.forward_request(request_id, action.modified_content)
    elif action.action == "drop":
        success = await interceptor.drop_request(request_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    await broadcast_ws("request_processed", {"request_id": request_id, "action": action.action})
    return {"success": success}

@api_router.post("/interceptor/request/{request_id}/repeater")
async def send_intercepted_to_repeater(request_id: str, tab_name: str = "MCP"):
    """Send intercepted request to Repeater"""
    success = await interceptor.send_to_repeater(request_id, tab_name)
    return {"success": success}

@api_router.post("/interceptor/request/{request_id}/intruder")
async def send_intercepted_to_intruder(request_id: str):
    """Send intercepted request to Intruder"""
    success = await interceptor.send_to_intruder(request_id)
    return {"success": success}

@api_router.get("/interceptor/rules")
async def get_match_replace_rules():
    """Get all match and replace rules"""
    return interceptor.get_match_replace_rules()

@api_router.post("/interceptor/rules")
async def add_match_replace_rule(rule: MatchReplaceRule):
    """Add a match and replace rule"""
    rule_id = interceptor.add_match_replace_rule(
        rule.match_type, rule.match_pattern, rule.replace_with, rule.enabled
    )
    return {"rule_id": rule_id}

@api_router.delete("/interceptor/rules/{rule_id}")
async def delete_match_replace_rule(rule_id: str):
    """Delete a match and replace rule"""
    interceptor.remove_match_replace_rule(rule_id)
    return {"success": True}

# ===================== IMPORT ROUTES =====================
@api_router.post("/import/burp-file")
async def import_burp_file(session_id: str, file: UploadFile = File(...)):
    """Import Burp export file (.xml or .json)"""
    content = await file.read()
    content_str = content.decode('utf-8', errors='ignore')
    
    # Parse the file
    items = BurpExportParser.parse_auto(content_str)
    
    if not items:
        raise HTTPException(status_code=400, detail="Could not parse file. Ensure it's a valid Burp export.")
    
    # Save to database
    for item in items:
        proxy_item = ProxyHistoryItem(
            session_id=session_id,
            method=item.get('method', ''),
            url=item.get('url', ''),
            host=item.get('host', ''),
            path=item.get('path', ''),
            status_code=item.get('status_code'),
            request_headers=item.get('request_headers', {}),
            request_body=item.get('request_body', ''),
            response_headers=item.get('response_headers', {}),
            response_body=item.get('response_body', ''),
            raw_request=item.get('request', ''),
            raw_response=item.get('response', ''),
        )
        doc = proxy_item.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.proxy_history.insert_one(doc)
    
    # Update session
    await db.sessions.update_one(
        {"id": session_id},
        {"$inc": {"requests_analyzed": len(items)}}
    )
    
    return {"imported": len(items), "session_id": session_id}

@api_router.post("/import/raw-request")
async def import_raw_request(session_id: str, raw_request: str, host: str, 
                             port: int = 443, protocol: str = "https"):
    """Import a raw HTTP request"""
    # Parse the request
    headers, body = BurpExportParser._parse_http_message(raw_request)
    
    # Extract method and path
    lines = raw_request.split('\n')
    method = "GET"
    path = "/"
    if lines:
        parts = lines[0].split(' ')
        if len(parts) >= 2:
            method = parts[0]
            path = parts[1]
    
    url = f"{protocol}://{host}{path}"
    
    proxy_item = ProxyHistoryItem(
        session_id=session_id,
        method=method,
        url=url,
        host=host,
        path=path,
        request_headers=headers,
        request_body=body,
        raw_request=raw_request,
    )
    doc = proxy_item.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.proxy_history.insert_one(doc)
    
    return {"id": proxy_item.id, "url": url}

# ===================== SESSION ROUTES =====================
@api_router.post("/sessions", response_model=SessionModel)
async def create_session(session: SessionCreate):
    # Check Burp connection
    await update_mcp_client()
    status = await mcp_client.get_status()
    
    session_obj = SessionModel(
        **session.model_dump(),
        burp_connected=status.success
    )
    doc = session_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.sessions.insert_one(doc)
    return session_obj

@api_router.get("/sessions")
async def list_sessions(limit: int = 50, skip: int = 0):
    sessions = await db.sessions.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return sessions

@api_router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@api_router.put("/sessions/{session_id}/status")
async def update_session_status(session_id: str, status: SessionStatus):
    result = await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"status": status.value, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "updated"}

@api_router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    await db.sessions.delete_one({"id": session_id})
    await db.findings.delete_many({"session_id": session_id})
    await db.chat_messages.delete_many({"session_id": session_id})
    await db.proxy_history.delete_many({"session_id": session_id})
    return {"status": "deleted"}

# ===================== FINDINGS ROUTES =====================
@api_router.post("/findings", response_model=FindingModel)
async def create_finding(finding: FindingCreate):
    finding_obj = FindingModel(**finding.model_dump())
    doc = finding_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.findings.insert_one(doc)
    
    await db.sessions.update_one(
        {"id": finding.session_id},
        {"$inc": {"findings_count": 1}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Broadcast to WebSocket (exclude MongoDB _id)
    broadcast_doc = {k: v for k, v in doc.items() if k != '_id'}
    await broadcast_ws("new_finding", {"finding": broadcast_doc})
    
    return finding_obj

@api_router.get("/findings")
async def list_findings(session_id: Optional[str] = None, severity: Optional[SeverityLevel] = None, limit: int = 100):
    query = {}
    if session_id:
        query["session_id"] = session_id
    if severity:
        query["severity"] = severity.value
    
    findings = await db.findings.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return findings

@api_router.get("/findings/{finding_id}")
async def get_finding(finding_id: str):
    finding = await db.findings.find_one({"id": finding_id}, {"_id": 0})
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding

@api_router.delete("/findings/{finding_id}")
async def delete_finding(finding_id: str):
    finding = await db.findings.find_one({"id": finding_id}, {"_id": 0})
    if finding:
        await db.findings.delete_one({"id": finding_id})
        await db.sessions.update_one(
            {"id": finding['session_id']},
            {"$inc": {"findings_count": -1}}
        )
    return {"status": "deleted"}

# ===================== CHAT ROUTES =====================
@api_router.post("/chat")
async def send_chat_message(message: ChatMessageCreate):
    # Save user message
    user_msg = ChatMessage(
        session_id=message.session_id,
        role="user",
        content=message.content
    )
    user_doc = user_msg.model_dump()
    user_doc['created_at'] = user_doc['created_at'].isoformat()
    await db.chat_messages.insert_one(user_doc)
    
    # Get chat history
    history = await db.chat_messages.find(
        {"session_id": message.session_id},
        {"_id": 0}
    ).sort("created_at", 1).limit(20).to_list(20)
    
    messages = [{"role": msg['role'], "content": msg['content']} for msg in history]
    
    # Check for tool commands in message
    tool_results = []
    if any(cmd in message.content.lower() for cmd in ['fetch history', 'get proxy', 'analyze traffic', 'scan']):
        # Auto-fetch proxy history for context
        await update_mcp_client()
        result = await mcp_client.get_proxy_history(50)
        if result.success:
            tool_results.append({"tool": "proxy_history", "data": result.data})
            messages[-1]['content'] += f"\n\n[PROXY HISTORY DATA]\n{json.dumps(result.data[:10], indent=2)}"
    
    # Get AI response
    config = await get_config()
    ai_response = await ai_service.get_ai_response(messages, config)
    
    # Save assistant response
    assistant_msg = ChatMessage(
        session_id=message.session_id,
        role="assistant",
        content=ai_response,
        tool_calls=tool_results if tool_results else None
    )
    assistant_doc = assistant_msg.model_dump()
    assistant_doc['created_at'] = assistant_doc['created_at'].isoformat()
    await db.chat_messages.insert_one(assistant_doc)
    
    return {
        "user_message": {k: v for k, v in user_doc.items() if k != '_id'},
        "assistant_message": {k: v for k, v in assistant_doc.items() if k != '_id'}
    }

@api_router.get("/chat/{session_id}")
async def get_chat_history(session_id: str, limit: int = 100):
    messages = await db.chat_messages.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("created_at", 1).limit(limit).to_list(limit)
    return messages

@api_router.delete("/chat/{session_id}")
async def clear_chat_history(session_id: str):
    await db.chat_messages.delete_many({"session_id": session_id})
    return {"status": "cleared"}

# ===================== PROXY HISTORY ROUTES =====================
@api_router.post("/proxy-history")
async def add_proxy_item(item: ProxyHistoryItem):
    doc = item.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.proxy_history.insert_one(doc)
    
    await db.sessions.update_one(
        {"id": item.session_id},
        {"$inc": {"requests_analyzed": 1}}
    )
    return item

@api_router.get("/proxy-history/{session_id}")
async def get_proxy_history(session_id: str, limit: int = 200):
    items = await db.proxy_history.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    return items

# ===================== AUTONOMOUS HUNTING =====================
hunting_tasks: Dict[str, Any] = {}

@api_router.post("/hunt/start/{session_id}")
async def start_autonomous_hunt(session_id: str, hunt_request: HuntRequest, background_tasks: BackgroundTasks):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Validate authorization for active modes
    if hunt_request.strategy in ["active_safe", "active_full"] and not hunt_request.authorized:
        raise HTTPException(
            status_code=403, 
            detail="Active hunting requires explicit authorization. Set authorized=true to confirm."
        )
    
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"status": "hunting", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Create hunter instance
    await update_mcp_client()
    hunter = AutonomousHunter(mcp_client, ai_service)
    
    # Store task reference
    hunting_tasks[session_id] = {"hunter": hunter, "status": "running"}
    
    # Run in background
    background_tasks.add_task(
        run_autonomous_hunt, 
        session_id, 
        hunter, 
        HuntingStrategy(hunt_request.strategy),
        hunt_request.target_scope,
        hunt_request.authorized
    )
    
    return {"status": "hunting_started", "session_id": session_id, "strategy": hunt_request.strategy}

async def run_autonomous_hunt(session_id: str, hunter: AutonomousHunter, 
                               strategy: HuntingStrategy, target_scope: List[str], authorized: bool):
    """Background task for autonomous hunting"""
    try:
        # Also fetch from local DB if Burp not connected
        local_items = await db.proxy_history.find(
            {"session_id": session_id},
            {"_id": 0}
        ).to_list(500)
        
        if local_items:
            hunter._history_items = local_items
        
        task = await hunter.start_hunt(session_id, strategy, target_scope, authorized)
        
        # Save findings to database
        for finding in task.findings:
            finding_doc = FindingModel(
                session_id=session_id,
                title=finding.title,
                description=finding.description,
                severity=SeverityLevel(finding.severity),
                vulnerability_type=finding.vulnerability_type,
                confidence=finding.confidence,
                evidence=finding.evidence,
                request_data=finding.request,
                response_data=finding.response,
                recommendations=finding.recommendations
            )
            doc = finding_doc.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            await db.findings.insert_one(doc)
        
        # Update session
        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {"status": task.status, "updated_at": datetime.now(timezone.utc).isoformat()},
                "$inc": {"findings_count": len(task.findings)}
            }
        )
        
        # Broadcast completion
        await broadcast_ws("hunt_complete", {
            "session_id": session_id,
            "status": task.status,
            "findings_count": len(task.findings)
        })
        
    except Exception as e:
        logger.error(f"Hunt error: {e}")
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"status": "idle", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    finally:
        if session_id in hunting_tasks:
            del hunting_tasks[session_id]

@api_router.post("/hunt/stop/{session_id}")
async def stop_autonomous_hunt(session_id: str):
    if session_id in hunting_tasks:
        hunter = hunting_tasks[session_id].get("hunter")
        if hunter:
            await hunter.stop_hunt()
    
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"status": "idle", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "hunting_stopped"}

@api_router.get("/hunt/status/{session_id}")
async def get_hunt_status(session_id: str):
    if session_id in hunting_tasks:
        hunter = hunting_tasks[session_id].get("hunter")
        if hunter and hunter.current_task:
            return {
                "status": hunter.current_task.status,
                "analyzed": hunter.current_task.analyzed_count,
                "total": hunter.current_task.total_count,
                "findings": len(hunter.current_task.findings),
                "current_action": hunter.current_task.current_action,
                "reasoning": hunter.current_task.reasoning_log[-5:] if hunter.current_task.reasoning_log else []
            }
    return {"status": "idle"}

# ===================== DASHBOARD STATS =====================
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    total_sessions = await db.sessions.count_documents({})
    active_sessions = await db.sessions.count_documents({"status": {"$in": ["hunting", "analyzing"]}})
    
    total_findings = await db.findings.count_documents({})
    critical = await db.findings.count_documents({"severity": "critical"})
    high = await db.findings.count_documents({"severity": "high"})
    medium = await db.findings.count_documents({"severity": "medium"})
    low = await db.findings.count_documents({"severity": "low"})
    info = await db.findings.count_documents({"severity": "info"})
    
    requests = await db.proxy_history.count_documents({})
    
    recent = await db.findings.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    # Check Burp connection
    await update_mcp_client()
    burp_status = await mcp_client.get_status()
    
    return DashboardStats(
        total_sessions=total_sessions,
        active_sessions=active_sessions,
        total_findings=total_findings,
        critical_findings=critical,
        high_findings=high,
        medium_findings=medium,
        low_findings=low,
        info_findings=info,
        requests_analyzed=requests,
        burp_connected=burp_status.success,
        intercept_enabled=interceptor.intercept_enabled,
        recent_findings=recent
    )

# ===================== REPORTS =====================
@api_router.get("/reports/{session_id}")
async def generate_report(session_id: str):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    findings = await db.findings.find({"session_id": session_id}, {"_id": 0}).to_list(1000)
    
    severity_order = ["critical", "high", "medium", "low", "info"]
    grouped = {s: [] for s in severity_order}
    for f in findings:
        grouped[f['severity']].append(f)
    
    return {
        "session": session,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_findings": len(findings),
            "by_severity": {s: len(grouped[s]) for s in severity_order}
        },
        "findings": grouped
    }

# ===================== WEBSOCKET =====================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_connections.append(websocket)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "data": {"intercept_enabled": interceptor.intercept_enabled}
        })
        
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        ws_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in ws_connections:
            ws_connections.remove(websocket)

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    await mcp_client.disconnect()
