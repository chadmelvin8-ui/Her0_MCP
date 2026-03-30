"""
Real MCP Client for Burp Suite Integration
Connects to Burp's MCP Server via SSE (Server-Sent Events)
"""

import aiohttp
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

@dataclass
class MCPToolCall:
    """Represents an MCP tool call"""
    tool_name: str
    parameters: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass 
class MCPToolResult:
    """Result from an MCP tool call"""
    tool_name: str
    success: bool
    data: Any
    error: Optional[str] = None
    call_id: str = ""

class BurpMCPClient:
    """
    Real MCP Client for connecting to Burp Suite's MCP Server
    Uses SSE (Server-Sent Events) protocol at http://127.0.0.1:9876
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9876):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.session: Optional[aiohttp.ClientSession] = None
        self.connected = False
        self.message_id = 0
        self._tools_cache: Dict[str, Any] = {}
        
    async def connect(self) -> bool:
        """Establish connection to Burp MCP Server"""
        try:
            self.session = aiohttp.ClientSession()
            # Test connection by getting server status
            result = await self.call_tool("status", {})
            if result.success:
                self.connected = True
                logger.info(f"Connected to Burp MCP Server at {self.base_url}")
                return True
            else:
                logger.error(f"Failed to connect: {result.error}")
                return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Close the connection"""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
        
    async def _get_next_message_id(self) -> int:
        """Get next message ID for JSON-RPC"""
        self.message_id += 1
        return self.message_id
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> MCPToolResult:
        """
        Call an MCP tool on Burp Suite
        
        Available tools include:
        - status: Get extension status
        - proxy_http_history: Get proxy history
        - proxy_http_history_regex: Get filtered proxy history
        - http1_request: Send HTTP/1.1 request
        - http2_request: Send HTTP/2 request
        - repeater_tab: Create Repeater tab
        - intruder: Send to Intruder
        - scope_check: Check if URL in scope
        - site_map: Get site map
        - And many more...
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            message_id = await self._get_next_message_id()
            
            # MCP JSON-RPC format
            payload = {
                "jsonrpc": "2.0",
                "id": message_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": params
                }
            }
            
            # Send via POST to MCP endpoint
            async with self.session.post(
                f"{self.base_url}/mcp",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if "error" in result:
                        return MCPToolResult(
                            tool_name=tool_name,
                            success=False,
                            data=None,
                            error=result["error"].get("message", "Unknown error"),
                            call_id=str(message_id)
                        )
                    return MCPToolResult(
                        tool_name=tool_name,
                        success=True,
                        data=result.get("result", {}),
                        call_id=str(message_id)
                    )
                else:
                    error_text = await response.text()
                    return MCPToolResult(
                        tool_name=tool_name,
                        success=False,
                        data=None,
                        error=f"HTTP {response.status}: {error_text}",
                        call_id=str(message_id)
                    )
        except aiohttp.ClientError as e:
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=f"Connection error: {str(e)}"
            )
        except Exception as e:
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=str(e)
            )
    
    # ==================== PROXY HISTORY TOOLS ====================
    
    async def get_proxy_history(self, limit: int = 100, offset: int = 0) -> MCPToolResult:
        """Get HTTP proxy history from Burp"""
        return await self.call_tool("proxy_http_history", {
            "limit": limit,
            "offset": offset
        })
    
    async def get_proxy_history_filtered(self, regex: str, limit: int = 100) -> MCPToolResult:
        """Get filtered proxy history using regex"""
        return await self.call_tool("proxy_http_history_regex", {
            "regex": regex,
            "limit": limit
        })
    
    async def search_response_bodies(self, regex: str, limit: int = 100) -> MCPToolResult:
        """Search response bodies using regex pattern"""
        return await self.call_tool("response_body_search", {
            "regex": regex,
            "limit": limit
        })
    
    async def get_websocket_history(self, limit: int = 100) -> MCPToolResult:
        """Get WebSocket proxy history"""
        return await self.call_tool("proxy_ws_history", {
            "limit": limit
        })
    
    # ==================== REQUEST TOOLS ====================
    
    async def send_http_request(self, request: str, host: str, port: int = 443, use_https: bool = True) -> MCPToolResult:
        """Send an HTTP/1.1 request"""
        return await self.call_tool("http1_request", {
            "request": request,
            "host": host,
            "port": port,
            "useHttps": use_https
        })
    
    async def send_http2_request(self, request: str, host: str, port: int = 443, use_https: bool = True) -> MCPToolResult:
        """Send an HTTP/2 request"""
        return await self.call_tool("http2_request", {
            "request": request,
            "host": host,
            "port": port,
            "useHttps": use_https
        })
    
    async def create_repeater_tab(self, request: str, host: str, port: int = 443, 
                                   use_https: bool = True, tab_name: str = "MCP") -> MCPToolResult:
        """Create a new Repeater tab with the request"""
        return await self.call_tool("repeater_tab", {
            "request": request,
            "host": host,
            "port": port,
            "useHttps": use_https,
            "tabName": tab_name
        })
    
    async def send_to_intruder(self, request: str, host: str, port: int = 443, use_https: bool = True) -> MCPToolResult:
        """Send request to Intruder"""
        return await self.call_tool("intruder", {
            "request": request,
            "host": host,
            "port": port,
            "useHttps": use_https
        })
    
    async def prepare_intruder(self, request: str, host: str, insertion_points: List[Dict], 
                               port: int = 443, use_https: bool = True) -> MCPToolResult:
        """Create Intruder tab with explicit insertion points"""
        return await self.call_tool("intruder_prepare", {
            "request": request,
            "host": host,
            "port": port,
            "useHttps": use_https,
            "insertionPoints": insertion_points
        })
    
    # ==================== ANALYSIS TOOLS ====================
    
    async def parse_request(self, request: str) -> MCPToolResult:
        """Parse raw HTTP request into components"""
        return await self.call_tool("request_parse", {
            "request": request
        })
    
    async def parse_response(self, response: str) -> MCPToolResult:
        """Parse raw HTTP response into components"""
        return await self.call_tool("response_parse", {
            "response": response
        })
    
    async def extract_parameters(self, request: str) -> MCPToolResult:
        """Extract parameters from a request"""
        return await self.call_tool("params_extract", {
            "request": request
        })
    
    async def get_insertion_points(self, request: str) -> MCPToolResult:
        """Get insertion point offsets for fuzzing"""
        return await self.call_tool("insertion_points", {
            "request": request
        })
    
    async def find_reflected_values(self, request: str, response: str) -> MCPToolResult:
        """Find reflected parameter values in response"""
        return await self.call_tool("find_reflected", {
            "request": request,
            "response": response
        })
    
    async def diff_requests(self, request1: str, request2: str) -> MCPToolResult:
        """Get diff between two requests"""
        return await self.call_tool("diff_requests", {
            "request1": request1,
            "request2": request2
        })
    
    # ==================== SCOPE & SITE MAP ====================
    
    async def check_scope(self, url: str) -> MCPToolResult:
        """Check if URL is in scope"""
        return await self.call_tool("scope_check", {
            "url": url
        })
    
    async def include_in_scope(self, url: str) -> MCPToolResult:
        """Add URL to scope"""
        return await self.call_tool("scope_include", {
            "url": url
        })
    
    async def exclude_from_scope(self, url: str) -> MCPToolResult:
        """Remove URL from scope"""
        return await self.call_tool("scope_exclude", {
            "url": url
        })
    
    async def get_site_map(self, limit: int = 100) -> MCPToolResult:
        """Get site map entries"""
        return await self.call_tool("site_map", {
            "limit": limit
        })
    
    async def get_site_map_filtered(self, regex: str, limit: int = 100) -> MCPToolResult:
        """Get filtered site map using regex"""
        return await self.call_tool("site_map_regex", {
            "regex": regex,
            "limit": limit
        })
    
    # ==================== PROXY CONTROL ====================
    
    async def set_intercept(self, enabled: bool) -> MCPToolResult:
        """Enable/disable proxy intercept"""
        return await self.call_tool("proxy_intercept", {
            "enabled": enabled
        })
    
    async def annotate_history(self, regex: str, notes: str = "", highlight: str = "") -> MCPToolResult:
        """Add notes/highlights to proxy history items"""
        return await self.call_tool("proxy_history_annotate", {
            "regex": regex,
            "notes": notes,
            "highlight": highlight
        })
    
    # ==================== UTILITY TOOLS ====================
    
    async def get_status(self) -> MCPToolResult:
        """Get Burp extension status"""
        return await self.call_tool("status", {})
    
    async def base64_encode(self, data: str) -> MCPToolResult:
        """Base64 encode string"""
        return await self.call_tool("base64_encode", {"input": data})
    
    async def base64_decode(self, data: str) -> MCPToolResult:
        """Base64 decode string"""
        return await self.call_tool("base64_decode", {"input": data})
    
    async def url_encode(self, data: str) -> MCPToolResult:
        """URL encode string"""
        return await self.call_tool("url_encode", {"input": data})
    
    async def url_decode(self, data: str) -> MCPToolResult:
        """URL decode string"""
        return await self.call_tool("url_decode", {"input": data})
    
    async def compute_hash(self, data: str, algorithm: str = "sha256") -> MCPToolResult:
        """Compute hash (md5, sha1, sha256, sha512)"""
        return await self.call_tool("hash_compute", {
            "input": data,
            "algorithm": algorithm
        })
    
    async def decode_jwt(self, token: str) -> MCPToolResult:
        """Decode JWT without verification"""
        return await self.call_tool("jwt_decode", {"jwt": token})
    
    async def generate_random_string(self, length: int = 16, charset: str = "alphanumeric") -> MCPToolResult:
        """Generate random string"""
        return await self.call_tool("random_string", {
            "length": length,
            "charset": charset
        })
    
    async def get_cookies(self) -> MCPToolResult:
        """Get cookies from Burp's cookie jar"""
        return await self.call_tool("cookie_jar_get", {})
    
    # ==================== ISSUE MANAGEMENT ====================
    
    async def create_issue(self, name: str, detail: str, severity: str = "information",
                          confidence: str = "certain", url: str = "", 
                          request: str = "", response: str = "") -> MCPToolResult:
        """Create a custom audit issue in Burp"""
        return await self.call_tool("issue_create", {
            "name": name,
            "detail": detail,
            "severity": severity,  # high, medium, low, information
            "confidence": confidence,  # certain, firm, tentative
            "url": url,
            "request": request,
            "response": response
        })
    
    # ==================== COLLABORATOR (Pro only) ====================
    
    async def generate_collaborator_payload(self) -> MCPToolResult:
        """Generate Burp Collaborator payload (Pro only)"""
        return await self.call_tool("collaborator_generate", {})
    
    async def poll_collaborator(self, secret: str) -> MCPToolResult:
        """Poll for Collaborator interactions (Pro only)"""
        return await self.call_tool("collaborator_poll", {"secret": secret})


class BurpExportParser:
    """
    Parser for Burp Suite export files (.xml, .json)
    Supports importing saved items for analysis
    """
    
    @staticmethod
    def parse_burp_xml(xml_content: str) -> List[Dict[str, Any]]:
        """Parse Burp XML export format"""
        import xml.etree.ElementTree as ET
        import base64
        
        items = []
        try:
            root = ET.fromstring(xml_content)
            for item in root.findall('.//item'):
                parsed = {
                    'id': str(uuid.uuid4()),
                    'method': '',
                    'url': '',
                    'host': '',
                    'port': 80,
                    'protocol': 'http',
                    'path': '',
                    'status_code': None,
                    'request': '',
                    'response': '',
                    'request_headers': {},
                    'response_headers': {},
                    'request_body': '',
                    'response_body': '',
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Extract basic info
                time_elem = item.find('time')
                if time_elem is not None and time_elem.text:
                    parsed['timestamp'] = time_elem.text
                
                url_elem = item.find('url')
                if url_elem is not None and url_elem.text:
                    parsed['url'] = url_elem.text
                
                host_elem = item.find('host')
                if host_elem is not None:
                    parsed['host'] = host_elem.text or ''
                    parsed['port'] = int(host_elem.get('port', 80) or 80)
                
                protocol_elem = item.find('protocol')
                if protocol_elem is not None and protocol_elem.text:
                    parsed['protocol'] = protocol_elem.text
                
                method_elem = item.find('method')
                if method_elem is not None and method_elem.text:
                    parsed['method'] = method_elem.text
                
                path_elem = item.find('path')
                if path_elem is not None and path_elem.text:
                    parsed['path'] = path_elem.text
                
                status_elem = item.find('status')
                if status_elem is not None and status_elem.text:
                    try:
                        parsed['status_code'] = int(status_elem.text)
                    except ValueError:
                        pass
                
                # Extract request (may be base64 encoded)
                request_elem = item.find('request')
                if request_elem is not None and request_elem.text:
                    if request_elem.get('base64') == 'true':
                        try:
                            parsed['request'] = base64.b64decode(request_elem.text).decode('utf-8', errors='ignore')
                        except:
                            parsed['request'] = request_elem.text
                    else:
                        parsed['request'] = request_elem.text
                
                # Extract response (may be base64 encoded)
                response_elem = item.find('response')
                if response_elem is not None and response_elem.text:
                    if response_elem.get('base64') == 'true':
                        try:
                            parsed['response'] = base64.b64decode(response_elem.text).decode('utf-8', errors='ignore')
                        except:
                            parsed['response'] = response_elem.text
                    else:
                        parsed['response'] = response_elem.text
                
                # Parse headers and body from raw request/response
                if parsed['request']:
                    parsed['request_headers'], parsed['request_body'] = BurpExportParser._parse_http_message(parsed['request'])
                if parsed['response']:
                    parsed['response_headers'], parsed['response_body'] = BurpExportParser._parse_http_message(parsed['response'])
                
                items.append(parsed)
                
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
        
        return items
    
    @staticmethod
    def parse_burp_json(json_content: str) -> List[Dict[str, Any]]:
        """Parse Burp JSON export format"""
        items = []
        try:
            data = json.loads(json_content)
            
            # Handle both array and single object
            if isinstance(data, list):
                raw_items = data
            elif isinstance(data, dict):
                raw_items = data.get('items', [data])
            else:
                return items
            
            for item in raw_items:
                parsed = {
                    'id': str(uuid.uuid4()),
                    'method': item.get('method', ''),
                    'url': item.get('url', ''),
                    'host': item.get('host', ''),
                    'port': item.get('port', 80),
                    'protocol': item.get('protocol', 'http'),
                    'path': item.get('path', ''),
                    'status_code': item.get('status', item.get('statusCode')),
                    'request': item.get('request', ''),
                    'response': item.get('response', ''),
                    'request_headers': item.get('requestHeaders', {}),
                    'response_headers': item.get('responseHeaders', {}),
                    'request_body': item.get('requestBody', ''),
                    'response_body': item.get('responseBody', ''),
                    'timestamp': item.get('time', item.get('timestamp', datetime.utcnow().isoformat()))
                }
                
                # Decode base64 if present
                import base64
                if item.get('requestBase64'):
                    try:
                        parsed['request'] = base64.b64decode(item['requestBase64']).decode('utf-8', errors='ignore')
                    except:
                        pass
                if item.get('responseBase64'):
                    try:
                        parsed['response'] = base64.b64decode(item['responseBase64']).decode('utf-8', errors='ignore')
                    except:
                        pass
                
                items.append(parsed)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
        
        return items
    
    @staticmethod
    def _parse_http_message(raw: str) -> tuple:
        """Parse raw HTTP message into headers dict and body"""
        headers = {}
        body = ""
        
        if not raw:
            return headers, body
        
        try:
            # Split headers and body
            if '\r\n\r\n' in raw:
                header_section, body = raw.split('\r\n\r\n', 1)
            elif '\n\n' in raw:
                header_section, body = raw.split('\n\n', 1)
            else:
                header_section = raw
                body = ""
            
            # Parse headers
            lines = header_section.replace('\r\n', '\n').split('\n')
            for line in lines[1:]:  # Skip first line (request/status line)
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
                    
        except Exception as e:
            logger.error(f"Error parsing HTTP message: {e}")
        
        return headers, body
    
    @staticmethod
    def detect_format(content: str) -> str:
        """Detect if content is XML or JSON"""
        content = content.strip()
        if content.startswith('<?xml') or content.startswith('<items'):
            return 'xml'
        elif content.startswith('{') or content.startswith('['):
            return 'json'
        return 'unknown'
    
    @staticmethod
    def parse_auto(content: str) -> List[Dict[str, Any]]:
        """Auto-detect format and parse"""
        format_type = BurpExportParser.detect_format(content)
        if format_type == 'xml':
            return BurpExportParser.parse_burp_xml(content)
        elif format_type == 'json':
            return BurpExportParser.parse_burp_json(content)
        return []
