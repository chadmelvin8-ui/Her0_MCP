from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="MCP'Arsonist AI", version="1.0.0")

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    evidence: str
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    recommendations: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FindingCreate(BaseModel):
    session_id: str
    title: str
    description: str
    severity: SeverityLevel
    vulnerability_type: str
    evidence: str
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    recommendations: List[str] = []

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str  # user, assistant, system
    content: str
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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    analyzed: bool = False
    flags: List[str] = []

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
    recent_findings: List[Dict[str, Any]] = []

# ===================== AI SERVICE =====================
class AIService:
    def __init__(self):
        self.system_prompt = """You are MCP'Arsonist AI, an elite autonomous penetration testing assistant integrated with Burp Suite via MCP (Model Context Protocol).

Your capabilities:
1. Analyze HTTP traffic from Burp Suite proxy history
2. Identify vulnerabilities (IDOR, XSS, SQLi, SSRF, Authentication flaws, Logic bugs)
3. Chain discoveries to find complex attack paths
4. Generate evidence-based security reports

Hunting Strategies:
- PASSIVE_HUNTER: Analyze responses for sensitive data leakage, misconfigurations
- IDOR_HUNTER: Look for direct object references, UUID enumeration, privilege escalation
- LOGIC_FLAW_HUNTER: Identify business logic vulnerabilities, race conditions
- AUTH_HUNTER: Find authentication/session management issues
- INJECTION_HUNTER: Detect SQLi, XSS, command injection vectors

Always reason step-by-step. Show your analysis process. Never perform active exploitation without explicit user authorization.

Format findings with:
- [SEVERITY] Vulnerability Title
- Description of the issue
- Evidence (exact request/response data)
- Impact assessment
- Remediation recommendations"""

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
            
            # Map provider/model
            if provider == 'anthropic':
                chat.with_model("anthropic", model if model else "claude-sonnet-4-5-20250929")
            elif provider == 'gemini':
                chat.with_model("gemini", model if model else "gemini-3-flash-preview")
            else:
                chat.with_model("openai", model if model else "gpt-5.2")
            
            # Get last user message
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
def serialize_doc(doc: dict) -> dict:
    """Serialize MongoDB document for JSON response"""
    if doc is None:
        return None
    result = {k: v for k, v in doc.items() if k != '_id'}
    for key, value in result.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
    return result

async def get_config() -> dict:
    config = await db.config.find_one({}, {"_id": 0})
    if not config:
        default_config = ConfigModel().model_dump()
        default_config['created_at'] = default_config['created_at'].isoformat()
        default_config['updated_at'] = default_config['updated_at'].isoformat()
        # Make a copy to insert (MongoDB mutates the dict)
        insert_doc = dict(default_config)
        await db.config.insert_one(insert_doc)
        return default_config
    return config

# ===================== ROUTES =====================

# Health check
@api_router.get("/")
async def root():
    return {"message": "MCP'Arsonist AI API v1.0", "status": "operational"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "MCP'Arsonist AI"}

# ===================== CONFIG ROUTES =====================
@api_router.get("/config")
async def get_configuration():
    config = await get_config()
    return config

@api_router.put("/config")
async def update_configuration(update: ConfigUpdate):
    config = await get_config()
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.config.update_one({"id": config['id']}, {"$set": update_data})
    updated = await db.config.find_one({"id": config['id']}, {"_id": 0})
    return updated

# ===================== SESSION ROUTES =====================
@api_router.post("/sessions", response_model=SessionModel)
async def create_session(session: SessionCreate):
    session_obj = SessionModel(**session.model_dump())
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
    
    # Update session findings count
    await db.sessions.update_one(
        {"id": finding.session_id},
        {"$inc": {"findings_count": 1}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
    )
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
    
    # Get chat history for context
    history = await db.chat_messages.find(
        {"session_id": message.session_id},
        {"_id": 0}
    ).sort("created_at", 1).limit(20).to_list(20)
    
    messages = [{"role": msg['role'], "content": msg['content']} for msg in history]
    
    # Get AI response
    config = await get_config()
    ai_response = await ai_service.get_ai_response(messages, config)
    
    # Save assistant response
    assistant_msg = ChatMessage(
        session_id=message.session_id,
        role="assistant",
        content=ai_response
    )
    assistant_doc = assistant_msg.model_dump()
    assistant_doc['created_at'] = assistant_doc['created_at'].isoformat()
    await db.chat_messages.insert_one(assistant_doc)
    
    return {
        "user_message": serialize_doc(user_doc),
        "assistant_message": serialize_doc(assistant_doc)
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
    
    # Update session request count
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
        recent_findings=recent
    )

# ===================== AUTONOMOUS HUNTING =====================
@api_router.post("/hunt/start/{session_id}")
async def start_autonomous_hunt(session_id: str, background_tasks: BackgroundTasks):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"status": "hunting", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Add background task for hunting
    background_tasks.add_task(run_autonomous_hunt, session_id)
    
    return {"status": "hunting_started", "session_id": session_id}

async def run_autonomous_hunt(session_id: str):
    """Background task for autonomous vulnerability hunting"""
    try:
        config = await get_config()
        
        # Get proxy history to analyze
        history = await db.proxy_history.find(
            {"session_id": session_id, "analyzed": False},
            {"_id": 0}
        ).limit(50).to_list(50)
        
        if not history:
            # Add initial hunt message
            await ai_service.get_ai_response(
                [{"role": "user", "content": "No proxy history found. Please capture some traffic in Burp Suite first, then I can analyze it for vulnerabilities."}],
                config
            )
            await db.sessions.update_one(
                {"id": session_id},
                {"$set": {"status": "idle", "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            return
        
        # Analyze each request
        for item in history:
            analysis_prompt = f"""Analyze this HTTP request/response for security vulnerabilities:

METHOD: {item['method']}
URL: {item['url']}
REQUEST HEADERS: {json.dumps(item.get('request_headers', {}), indent=2)}
REQUEST BODY: {item.get('request_body', 'N/A')}
RESPONSE STATUS: {item.get('status_code', 'N/A')}
RESPONSE HEADERS: {json.dumps(item.get('response_headers', {}), indent=2)}
RESPONSE BODY: {(item.get('response_body', '')[:2000] + '...') if item.get('response_body') and len(item.get('response_body', '')) > 2000 else item.get('response_body', 'N/A')}

Identify any vulnerabilities following OWASP Top 10 categories. Report findings in structured format."""

            analysis = await ai_service.get_ai_response(
                [{"role": "user", "content": analysis_prompt}],
                config
            )
            
            # Mark as analyzed
            await db.proxy_history.update_one(
                {"id": item['id']},
                {"$set": {"analyzed": True}}
            )
            
            # Store analysis as chat message
            chat_msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=f"**Analyzed: {item['method']} {item['url']}**\n\n{analysis}",
                metadata={"type": "analysis", "request_id": item['id']}
            )
            chat_doc = chat_msg.model_dump()
            chat_doc['created_at'] = chat_doc['created_at'].isoformat()
            await db.chat_messages.insert_one(chat_doc)
            
            await asyncio.sleep(1)  # Rate limiting
        
        # Complete hunting
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"status": "completed", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
    except Exception as e:
        logger.error(f"Hunt error: {e}")
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"status": "idle", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )

@api_router.post("/hunt/stop/{session_id}")
async def stop_autonomous_hunt(session_id: str):
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"status": "idle", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "hunting_stopped"}

# ===================== REPORT GENERATION =====================
@api_router.get("/reports/{session_id}")
async def generate_report(session_id: str):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    findings = await db.findings.find({"session_id": session_id}, {"_id": 0}).to_list(1000)
    
    # Group by severity
    severity_order = ["critical", "high", "medium", "low", "info"]
    grouped = {s: [] for s in severity_order}
    for f in findings:
        grouped[f['severity']].append(f)
    
    report = {
        "session": session,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_findings": len(findings),
            "by_severity": {s: len(grouped[s]) for s in severity_order}
        },
        "findings": grouped
    }
    
    return report

# ===================== MOCK BURP DATA (for testing) =====================
@api_router.post("/mock/proxy-data/{session_id}")
async def generate_mock_proxy_data(session_id: str):
    """Generate mock proxy data for testing"""
    mock_requests = [
        {
            "method": "GET",
            "url": "https://example.com/api/users/123",
            "host": "example.com",
            "path": "/api/users/123",
            "status_code": 200,
            "request_headers": {"Authorization": "Bearer eyJ...", "Cookie": "session=abc123"},
            "response_headers": {"Content-Type": "application/json"},
            "response_body": '{"id": 123, "email": "user@example.com", "role": "admin", "password_hash": "bcrypt..."}'
        },
        {
            "method": "POST",
            "url": "https://example.com/api/transfer",
            "host": "example.com",
            "path": "/api/transfer",
            "status_code": 200,
            "request_headers": {"Content-Type": "application/json"},
            "request_body": '{"from_account": "123", "to_account": "456", "amount": 1000}',
            "response_headers": {"Content-Type": "application/json"},
            "response_body": '{"status": "success", "transaction_id": "TXN789"}'
        },
        {
            "method": "GET",
            "url": "https://example.com/api/search?q=<script>alert(1)</script>",
            "host": "example.com",
            "path": "/api/search",
            "status_code": 200,
            "request_headers": {},
            "response_headers": {"Content-Type": "text/html"},
            "response_body": '<html>Results for: <script>alert(1)</script></html>'
        }
    ]
    
    created = []
    for req in mock_requests:
        item = ProxyHistoryItem(session_id=session_id, **req)
        doc = item.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.proxy_history.insert_one(doc)
        created.append(item.id)
    
    await db.sessions.update_one(
        {"id": session_id},
        {"$inc": {"requests_analyzed": len(mock_requests)}}
    )
    
    return {"status": "created", "count": len(created), "ids": created}

# Include the router
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
