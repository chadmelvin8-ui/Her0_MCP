"""
Autonomous Vulnerability Hunter
Uses AI to analyze traffic and actively hunt for vulnerabilities
"""

import asyncio
import json
import logging
import re
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid

from mcp_client import BurpMCPClient, MCPToolResult

logger = logging.getLogger(__name__)


class HuntingStrategy(str, Enum):
    PASSIVE = "passive"  # Only analyze, no active testing
    ACTIVE_SAFE = "active_safe"  # Safe active tests (no destructive)
    ACTIVE_FULL = "active_full"  # Full autonomous mode (requires authorization)


class VulnerabilityType(str, Enum):
    IDOR = "IDOR"
    XSS = "XSS"
    SQLI = "SQL Injection"
    SSRF = "SSRF"
    AUTH = "Authentication Flaw"
    AUTHZ = "Authorization Flaw"
    INFO_DISCLOSURE = "Information Disclosure"
    LOGIC_FLAW = "Business Logic Flaw"
    CSRF = "CSRF"
    OPEN_REDIRECT = "Open Redirect"
    PATH_TRAVERSAL = "Path Traversal"
    COMMAND_INJECTION = "Command Injection"
    INSECURE_CONFIG = "Insecure Configuration"
    SENSITIVE_DATA = "Sensitive Data Exposure"


@dataclass
class Finding:
    """Represents a discovered vulnerability"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    severity: str = "info"  # critical, high, medium, low, info
    vulnerability_type: str = ""
    confidence: str = "tentative"  # certain, firm, tentative
    url: str = ""
    evidence: str = ""
    request: str = ""
    response: str = ""
    recommendations: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    

@dataclass
class HuntingTask:
    """Represents an autonomous hunting task"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    status: str = "pending"  # pending, running, paused, completed, failed
    strategy: HuntingStrategy = HuntingStrategy.PASSIVE
    target_scope: List[str] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    analyzed_count: int = 0
    total_count: int = 0
    current_action: str = ""
    reasoning_log: List[Dict[str, str]] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    

class AutonomousHunter:
    """
    AI-powered autonomous vulnerability hunter
    Connects to Burp Suite via MCP and uses AI to find vulnerabilities
    """
    
    def __init__(self, mcp_client: BurpMCPClient, ai_service: Any):
        self.mcp = mcp_client
        self.ai = ai_service
        self.current_task: Optional[HuntingTask] = None
        self._stop_requested = False
        self._callbacks: Dict[str, Callable] = {}
        
        # Vulnerability patterns for passive analysis
        self.patterns = {
            VulnerabilityType.SENSITIVE_DATA: [
                r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?[^"\'>\s]+',
                r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?[a-zA-Z0-9]{16,}',
                r'(?i)(secret|token)\s*[:=]\s*["\']?[a-zA-Z0-9]{16,}',
                r'(?i)(aws[_-]?access|aws[_-]?secret)',
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b',  # Credit card
                r'(?i)bearer\s+[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+',  # JWT
            ],
            VulnerabilityType.INFO_DISCLOSURE: [
                r'(?i)(stack\s*trace|traceback|exception)',
                r'(?i)(mysql|postgresql|oracle|sqlite|mongodb)\s*(error|exception)',
                r'(?i)(internal\s*server\s*error)',
                r'(?i)/home/\w+/',
                r'(?i)c:\\\\(users|windows)',
                r'(?i)version\s*[:=]\s*[\d\.]+',
            ],
            VulnerabilityType.IDOR: [
                r'(?i)(user_?id|userid|uid|account_?id|id)\s*[:=]\s*\d+',
                r'/api/\w+/\d+',
                r'/users?/\d+',
                r'/accounts?/\d+',
                r'/orders?/\d+',
                r'/profile/\d+',
            ],
            VulnerabilityType.XSS: [
                r'<script[^>]*>',
                r'javascript:',
                r'on\w+\s*=',
                r'(?i)content-type:\s*text/html(?!.*x-content-type-options)',
            ],
            VulnerabilityType.OPEN_REDIRECT: [
                r'(?i)(redirect|return|next|url|goto|destination)\s*=\s*https?://',
                r'(?i)(redirect|return|next|url|goto|destination)\s*=\s*//',
            ],
            VulnerabilityType.INSECURE_CONFIG: [
                r'(?i)access-control-allow-origin:\s*\*',
                r'(?i)x-frame-options:\s*(?!deny|sameorigin)',
                r'(?i)content-security-policy:\s*(?!.*default-src)',
            ]
        }
        
        # Active test payloads (used only in active mode with authorization)
        self.test_payloads = {
            VulnerabilityType.XSS: [
                '<script>alert(1)</script>',
                '"><img src=x onerror=alert(1)>',
                "'-alert(1)-'",
                '${alert(1)}',
            ],
            VulnerabilityType.SQLI: [
                "' OR '1'='1",
                "1' AND '1'='1",
                "1; SELECT * FROM users--",
                "1 UNION SELECT NULL--",
            ],
            VulnerabilityType.PATH_TRAVERSAL: [
                '../../../etc/passwd',
                '..\\..\\..\\windows\\win.ini',
                '....//....//....//etc/passwd',
            ],
            VulnerabilityType.COMMAND_INJECTION: [
                '; id',
                '| id',
                '`id`',
                '$(id)',
            ],
            VulnerabilityType.SSRF: [
                'http://127.0.0.1',
                'http://localhost',
                'http://169.254.169.254',  # AWS metadata
            ]
        }
    
    def on_progress(self, callback: Callable[[str, Dict], None]):
        """Register progress callback"""
        self._callbacks['progress'] = callback
    
    def on_finding(self, callback: Callable[[Finding], None]):
        """Register finding callback"""
        self._callbacks['finding'] = callback
    
    def on_reasoning(self, callback: Callable[[str], None]):
        """Register reasoning callback"""
        self._callbacks['reasoning'] = callback
    
    async def _emit_progress(self, message: str, data: Dict = None):
        """Emit progress update"""
        if 'progress' in self._callbacks:
            await asyncio.get_event_loop().run_in_executor(
                None, self._callbacks['progress'], message, data or {}
            )
        logger.info(f"[PROGRESS] {message}")
    
    async def _emit_finding(self, finding: Finding):
        """Emit new finding"""
        if 'finding' in self._callbacks:
            await asyncio.get_event_loop().run_in_executor(
                None, self._callbacks['finding'], finding
            )
        logger.info(f"[FINDING] {finding.severity.upper()}: {finding.title}")
    
    async def _add_reasoning(self, reasoning: str):
        """Add reasoning step"""
        if self.current_task:
            self.current_task.reasoning_log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reasoning": reasoning
            })
        if 'reasoning' in self._callbacks:
            await asyncio.get_event_loop().run_in_executor(
                None, self._callbacks['reasoning'], reasoning
            )
        logger.info(f"[REASONING] {reasoning}")
    
    async def start_hunt(self, session_id: str, strategy: HuntingStrategy = HuntingStrategy.PASSIVE,
                         target_scope: List[str] = None, authorized: bool = False) -> HuntingTask:
        """
        Start autonomous vulnerability hunting
        
        Args:
            session_id: Session ID to associate findings with
            strategy: Hunting strategy (passive, active_safe, active_full)
            target_scope: List of URLs/patterns in scope
            authorized: User has explicitly authorized active testing
        """
        # Validate authorization for active modes
        if strategy in [HuntingStrategy.ACTIVE_SAFE, HuntingStrategy.ACTIVE_FULL] and not authorized:
            raise ValueError("Active hunting requires explicit authorization")
        
        self._stop_requested = False
        self.current_task = HuntingTask(
            session_id=session_id,
            strategy=strategy,
            target_scope=target_scope or [],
            status="running",
            started_at=datetime.now(timezone.utc).isoformat()
        )
        
        await self._add_reasoning(f"Starting {strategy.value} vulnerability hunt")
        await self._emit_progress("Initializing hunt", {"task_id": self.current_task.id})
        
        try:
            # Check Burp connection
            await self._add_reasoning("Checking Burp Suite MCP connection...")
            status = await self.mcp.get_status()
            if not status.success:
                await self._add_reasoning(f"WARNING: Could not connect to Burp MCP: {status.error}")
                await self._add_reasoning("Continuing with imported/mock data analysis...")
            else:
                await self._add_reasoning(f"Connected to Burp Suite: {status.data}")
            
            # Phase 1: Gather proxy history
            await self._phase_gather_history()
            
            if self._stop_requested:
                return await self._complete_hunt("stopped")
            
            # Phase 2: Passive analysis
            await self._phase_passive_analysis()
            
            if self._stop_requested:
                return await self._complete_hunt("stopped")
            
            # Phase 3: Active testing (if authorized)
            if strategy in [HuntingStrategy.ACTIVE_SAFE, HuntingStrategy.ACTIVE_FULL]:
                await self._phase_active_testing()
            
            return await self._complete_hunt("completed")
            
        except Exception as e:
            logger.error(f"Hunt error: {e}")
            await self._add_reasoning(f"ERROR: {str(e)}")
            return await self._complete_hunt("failed")
    
    async def stop_hunt(self):
        """Request hunt to stop"""
        self._stop_requested = True
        await self._add_reasoning("Stop requested by user")
    
    async def _complete_hunt(self, status: str) -> HuntingTask:
        """Complete the hunt and return results"""
        if self.current_task:
            self.current_task.status = status
            self.current_task.completed_at = datetime.now(timezone.utc).isoformat()
            await self._emit_progress(f"Hunt {status}", {
                "findings_count": len(self.current_task.findings),
                "analyzed_count": self.current_task.analyzed_count
            })
        return self.current_task
    
    async def _phase_gather_history(self):
        """Phase 1: Gather traffic from Burp proxy history"""
        await self._add_reasoning("Phase 1: Gathering proxy history from Burp Suite")
        await self._emit_progress("Fetching proxy history")
        
        self.current_task.current_action = "Fetching proxy history"
        
        # Try to get history from Burp MCP
        result = await self.mcp.get_proxy_history(limit=500)
        
        if result.success and result.data:
            items = result.data if isinstance(result.data, list) else result.data.get('items', [])
            self.current_task.total_count = len(items)
            await self._add_reasoning(f"Retrieved {len(items)} items from proxy history")
            
            # Store for analysis
            self._history_items = items
        else:
            await self._add_reasoning("No items from Burp - will analyze any imported data")
            self._history_items = []
    
    async def _phase_passive_analysis(self):
        """Phase 2: Passive vulnerability analysis"""
        await self._add_reasoning("Phase 2: Starting passive vulnerability analysis")
        await self._emit_progress("Analyzing traffic passively")
        
        self.current_task.current_action = "Passive analysis"
        
        for idx, item in enumerate(self._history_items):
            if self._stop_requested:
                break
            
            self.current_task.analyzed_count = idx + 1
            await self._analyze_request_response(item)
            
            # Yield control periodically
            if idx % 10 == 0:
                await asyncio.sleep(0.1)
        
        await self._add_reasoning(f"Passive analysis complete. Found {len(self.current_task.findings)} potential issues")
    
    async def _analyze_request_response(self, item: Dict):
        """Analyze a single request/response pair"""
        request = item.get('request', '')
        response = item.get('response', '')
        url = item.get('url', '')
        method = item.get('method', 'GET')
        
        # Pattern-based detection
        for vuln_type, patterns in self.patterns.items():
            for pattern in patterns:
                # Check response
                if response:
                    matches = re.findall(pattern, response, re.IGNORECASE)
                    if matches:
                        finding = Finding(
                            title=f"Potential {vuln_type.value} Detected",
                            description=f"Pattern match found in response: {pattern[:50]}...",
                            severity=self._get_severity_for_type(vuln_type),
                            vulnerability_type=vuln_type.value,
                            confidence="tentative",
                            url=url,
                            evidence=f"Matched: {str(matches[:3])}",
                            request=request[:2000],
                            response=response[:2000],
                            recommendations=self._get_recommendations(vuln_type)
                        )
                        self.current_task.findings.append(finding)
                        await self._emit_finding(finding)
        
        # Check for IDOR indicators
        if re.search(r'/\d+(/|$|\?)', url):
            await self._add_reasoning(f"Potential IDOR target: {url}")
        
        # Check authentication headers
        auth_header = None
        if 'Authorization' in str(request):
            await self._add_reasoning(f"Request with auth found: {method} {url}")
    
    async def _phase_active_testing(self):
        """Phase 3: Active vulnerability testing (requires authorization)"""
        await self._add_reasoning("Phase 3: Starting authorized active testing")
        await self._emit_progress("Beginning active tests")
        
        self.current_task.current_action = "Active testing"
        
        # Find interesting endpoints for active testing
        interesting_endpoints = []
        for item in self._history_items:
            url = item.get('url', '')
            method = item.get('method', 'GET')
            
            # Look for parameterized endpoints
            if '=' in url or method == 'POST':
                interesting_endpoints.append(item)
        
        await self._add_reasoning(f"Found {len(interesting_endpoints)} endpoints for active testing")
        
        for endpoint in interesting_endpoints[:20]:  # Limit to 20 for safety
            if self._stop_requested:
                break
            
            await self._active_test_endpoint(endpoint)
            await asyncio.sleep(0.5)  # Rate limiting
    
    async def _active_test_endpoint(self, item: Dict):
        """Actively test an endpoint for vulnerabilities"""
        request = item.get('request', '')
        url = item.get('url', '')
        host = item.get('host', '')
        port = item.get('port', 443)
        
        if not request or not host:
            return
        
        await self._add_reasoning(f"Testing: {url}")
        
        # Get insertion points
        insertion_result = await self.mcp.get_insertion_points(request)
        if not insertion_result.success:
            return
        
        # Extract parameters
        params_result = await self.mcp.extract_parameters(request)
        if params_result.success and params_result.data:
            await self._add_reasoning(f"Found parameters: {params_result.data}")
        
        # Test for XSS (if in active_full mode)
        if self.current_task.strategy == HuntingStrategy.ACTIVE_FULL:
            for payload in self.test_payloads[VulnerabilityType.XSS][:2]:
                modified_request = self._inject_payload(request, payload)
                if modified_request:
                    result = await self.mcp.send_http_request(
                        modified_request, host, port, port == 443
                    )
                    if result.success and result.data:
                        response = result.data.get('response', '')
                        if payload in response:
                            finding = Finding(
                                title="Reflected XSS Vulnerability",
                                description=f"Payload was reflected in response without encoding",
                                severity="high",
                                vulnerability_type=VulnerabilityType.XSS.value,
                                confidence="firm",
                                url=url,
                                evidence=f"Payload: {payload}",
                                request=modified_request[:2000],
                                response=response[:2000],
                                recommendations=self._get_recommendations(VulnerabilityType.XSS)
                            )
                            self.current_task.findings.append(finding)
                            await self._emit_finding(finding)
    
    def _inject_payload(self, request: str, payload: str) -> Optional[str]:
        """Inject payload into request parameters"""
        # Simple parameter injection - replace first value
        modified = re.sub(r'(=)([^&\s]+)', f'\\1{payload}', request, count=1)
        return modified if modified != request else None
    
    def _get_severity_for_type(self, vuln_type: VulnerabilityType) -> str:
        """Get default severity for vulnerability type"""
        severities = {
            VulnerabilityType.SQLI: "critical",
            VulnerabilityType.COMMAND_INJECTION: "critical",
            VulnerabilityType.SSRF: "high",
            VulnerabilityType.XSS: "high",
            VulnerabilityType.IDOR: "high",
            VulnerabilityType.AUTH: "high",
            VulnerabilityType.AUTHZ: "high",
            VulnerabilityType.PATH_TRAVERSAL: "high",
            VulnerabilityType.CSRF: "medium",
            VulnerabilityType.OPEN_REDIRECT: "medium",
            VulnerabilityType.LOGIC_FLAW: "medium",
            VulnerabilityType.INFO_DISCLOSURE: "low",
            VulnerabilityType.SENSITIVE_DATA: "medium",
            VulnerabilityType.INSECURE_CONFIG: "low",
        }
        return severities.get(vuln_type, "info")
    
    def _get_recommendations(self, vuln_type: VulnerabilityType) -> List[str]:
        """Get remediation recommendations for vulnerability type"""
        recommendations = {
            VulnerabilityType.XSS: [
                "Implement proper output encoding (HTML, JavaScript, URL)",
                "Use Content-Security-Policy headers",
                "Validate and sanitize all user input"
            ],
            VulnerabilityType.SQLI: [
                "Use parameterized queries/prepared statements",
                "Implement input validation",
                "Use ORM frameworks that handle escaping"
            ],
            VulnerabilityType.IDOR: [
                "Implement proper authorization checks",
                "Use indirect object references (GUIDs)",
                "Verify user permissions for each resource access"
            ],
            VulnerabilityType.SSRF: [
                "Validate and whitelist allowed URLs",
                "Block internal IP ranges",
                "Use a URL parser to prevent bypasses"
            ],
            VulnerabilityType.SENSITIVE_DATA: [
                "Remove sensitive data from responses",
                "Implement proper access controls",
                "Use encryption for sensitive data"
            ],
            VulnerabilityType.INFO_DISCLOSURE: [
                "Configure proper error handling",
                "Remove stack traces in production",
                "Hide version information"
            ],
            VulnerabilityType.INSECURE_CONFIG: [
                "Review and harden security headers",
                "Implement proper CORS policy",
                "Enable X-Frame-Options and CSP"
            ]
        }
        return recommendations.get(vuln_type, ["Review and fix the identified issue"])
    
    async def analyze_with_ai(self, request: str, response: str, context: str = "") -> Dict:
        """Use AI to deeply analyze request/response for vulnerabilities"""
        prompt = f"""Analyze this HTTP request/response for security vulnerabilities.

REQUEST:
{request[:3000]}

RESPONSE:
{response[:3000]}

{f'CONTEXT: {context}' if context else ''}

Identify:
1. Any security vulnerabilities (OWASP Top 10)
2. Potential attack vectors
3. Sensitive data exposure
4. Authentication/authorization issues
5. Business logic flaws

For each finding, provide:
- Vulnerability type
- Severity (critical/high/medium/low/info)
- Evidence
- Exploitation steps
- Remediation

Be specific and cite exact evidence from the request/response."""

        # Use AI service
        messages = [{"role": "user", "content": prompt}]
        config = {"ai_provider": "openai", "ai_model": "gpt-5.2"}
        
        response = await self.ai.get_ai_response(messages, config)
        return {"analysis": response}
