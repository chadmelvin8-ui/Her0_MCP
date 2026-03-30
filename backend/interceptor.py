"""
Real-time Proxy Interceptor
Intercepts and modifies HTTP traffic through Burp Suite MCP
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid

from mcp_client import BurpMCPClient, MCPToolResult

logger = logging.getLogger(__name__)


class InterceptAction(str, Enum):
    FORWARD = "forward"
    DROP = "drop"
    FORWARD_MODIFIED = "forward_modified"


@dataclass
class InterceptedRequest:
    """Represents an intercepted HTTP request"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    method: str = ""
    url: str = ""
    host: str = ""
    port: int = 443
    protocol: str = "https"
    raw_request: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    body: str = ""
    intercepted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "pending"  # pending, forwarded, dropped, modified


@dataclass
class InterceptedResponse:
    """Represents an intercepted HTTP response"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    status_code: int = 0
    raw_response: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    body: str = ""
    intercepted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "pending"


class ProxyInterceptor:
    """
    Real-time proxy interceptor using Burp Suite MCP
    Allows intercepting, viewing, modifying, and forwarding/dropping requests
    """
    
    def __init__(self, mcp_client: BurpMCPClient):
        self.mcp = mcp_client
        self.intercept_enabled = False
        self.intercept_requests = True
        self.intercept_responses = True
        self.intercept_scope_only = True
        
        # Queues for intercepted items
        self._request_queue: List[InterceptedRequest] = []
        self._response_queue: List[InterceptedResponse] = []
        
        # Match/replace rules
        self._match_replace_rules: List[Dict] = []
        
        # Auto-forward rules (regex patterns to auto-forward)
        self._auto_forward_patterns: List[str] = [
            r'.*\.(css|js|png|jpg|jpeg|gif|ico|woff|woff2|ttf|svg)(\?.*)?$',
        ]
        
        # Callbacks
        self._callbacks: Dict[str, Callable] = {}
        
        # Polling task
        self._polling_task: Optional[asyncio.Task] = None
        
    def on_request_intercepted(self, callback: Callable[[InterceptedRequest], None]):
        """Register callback for intercepted requests"""
        self._callbacks['request'] = callback
        
    def on_response_intercepted(self, callback: Callable[[InterceptedResponse], None]):
        """Register callback for intercepted responses"""
        self._callbacks['response'] = callback
        
    def on_status_change(self, callback: Callable[[bool], None]):
        """Register callback for intercept status changes"""
        self._callbacks['status'] = callback
    
    async def enable_intercept(self) -> bool:
        """Enable proxy interception in Burp"""
        result = await self.mcp.set_intercept(True)
        if result.success:
            self.intercept_enabled = True
            logger.info("Proxy interception enabled")
            
            # Start polling for intercepted items
            if not self._polling_task or self._polling_task.done():
                self._polling_task = asyncio.create_task(self._poll_intercepted())
            
            if 'status' in self._callbacks:
                self._callbacks['status'](True)
            return True
        else:
            logger.error(f"Failed to enable intercept: {result.error}")
            return False
    
    async def disable_intercept(self) -> bool:
        """Disable proxy interception in Burp"""
        result = await self.mcp.set_intercept(False)
        if result.success:
            self.intercept_enabled = False
            logger.info("Proxy interception disabled")
            
            # Stop polling
            if self._polling_task and not self._polling_task.done():
                self._polling_task.cancel()
                
            if 'status' in self._callbacks:
                self._callbacks['status'](False)
            return True
        else:
            logger.error(f"Failed to disable intercept: {result.error}")
            return False
    
    async def toggle_intercept(self) -> bool:
        """Toggle interception on/off"""
        if self.intercept_enabled:
            return await self.disable_intercept()
        else:
            return await self.enable_intercept()
    
    async def _poll_intercepted(self):
        """Poll for intercepted requests/responses (fallback when SSE not available)"""
        while self.intercept_enabled:
            try:
                # Get current editor content (intercepted item)
                result = await self.mcp.call_tool("editor_get", {})
                
                if result.success and result.data:
                    content = result.data.get('content', '')
                    editor_type = result.data.get('type', 'request')
                    
                    if content and content not in [r.raw_request for r in self._request_queue]:
                        if editor_type == 'request':
                            intercepted = self._parse_intercepted_request(content)
                            self._request_queue.append(intercepted)
                            
                            if 'request' in self._callbacks:
                                self._callbacks['request'](intercepted)
                        else:
                            intercepted = self._parse_intercepted_response(content)
                            self._response_queue.append(intercepted)
                            
                            if 'response' in self._callbacks:
                                self._callbacks['response'](intercepted)
                
                await asyncio.sleep(0.5)  # Poll every 500ms
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(1)
    
    def _parse_intercepted_request(self, raw: str) -> InterceptedRequest:
        """Parse raw HTTP request into InterceptedRequest"""
        request = InterceptedRequest(raw_request=raw)
        
        try:
            lines = raw.replace('\r\n', '\n').split('\n')
            if lines:
                # Parse request line
                parts = lines[0].split(' ')
                if len(parts) >= 2:
                    request.method = parts[0]
                    request.url = parts[1]
                
                # Parse headers
                in_headers = True
                body_lines = []
                for line in lines[1:]:
                    if in_headers:
                        if line.strip() == '':
                            in_headers = False
                        elif ':' in line:
                            key, value = line.split(':', 1)
                            request.headers[key.strip()] = value.strip()
                            if key.lower() == 'host':
                                request.host = value.strip()
                    else:
                        body_lines.append(line)
                
                request.body = '\n'.join(body_lines)
                
        except Exception as e:
            logger.error(f"Error parsing request: {e}")
        
        return request
    
    def _parse_intercepted_response(self, raw: str) -> InterceptedResponse:
        """Parse raw HTTP response into InterceptedResponse"""
        response = InterceptedResponse(raw_response=raw)
        
        try:
            lines = raw.replace('\r\n', '\n').split('\n')
            if lines:
                # Parse status line
                parts = lines[0].split(' ')
                if len(parts) >= 2:
                    try:
                        response.status_code = int(parts[1])
                    except ValueError:
                        pass
                
                # Parse headers
                in_headers = True
                body_lines = []
                for line in lines[1:]:
                    if in_headers:
                        if line.strip() == '':
                            in_headers = False
                        elif ':' in line:
                            key, value = line.split(':', 1)
                            response.headers[key.strip()] = value.strip()
                    else:
                        body_lines.append(line)
                
                response.body = '\n'.join(body_lines)
                
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
        
        return response
    
    async def forward_request(self, request_id: str, modified_content: Optional[str] = None) -> bool:
        """Forward an intercepted request (optionally modified)"""
        # Find request in queue
        request = next((r for r in self._request_queue if r.id == request_id), None)
        if not request:
            logger.error(f"Request not found: {request_id}")
            return False
        
        content = modified_content if modified_content else request.raw_request
        
        # Set editor content and forward
        result = await self.mcp.call_tool("editor_set", {"content": content})
        if result.success:
            request.status = "forwarded" if not modified_content else "modified"
            self._request_queue = [r for r in self._request_queue if r.id != request_id]
            logger.info(f"Request forwarded: {request_id}")
            return True
        else:
            logger.error(f"Failed to forward: {result.error}")
            return False
    
    async def drop_request(self, request_id: str) -> bool:
        """Drop an intercepted request"""
        request = next((r for r in self._request_queue if r.id == request_id), None)
        if not request:
            return False
        
        # Set empty content to drop
        result = await self.mcp.call_tool("editor_set", {"content": ""})
        if result.success:
            request.status = "dropped"
            self._request_queue = [r for r in self._request_queue if r.id != request_id]
            logger.info(f"Request dropped: {request_id}")
            return True
        return False
    
    async def forward_response(self, response_id: str, modified_content: Optional[str] = None) -> bool:
        """Forward an intercepted response (optionally modified)"""
        response = next((r for r in self._response_queue if r.id == response_id), None)
        if not response:
            return False
        
        content = modified_content if modified_content else response.raw_response
        
        result = await self.mcp.call_tool("editor_set", {"content": content})
        if result.success:
            response.status = "forwarded" if not modified_content else "modified"
            self._response_queue = [r for r in self._response_queue if r.id != response_id]
            return True
        return False
    
    async def drop_response(self, response_id: str) -> bool:
        """Drop an intercepted response"""
        response = next((r for r in self._response_queue if r.id == response_id), None)
        if not response:
            return False
        
        result = await self.mcp.call_tool("editor_set", {"content": ""})
        if result.success:
            response.status = "dropped"
            self._response_queue = [r for r in self._response_queue if r.id != response_id]
            return True
        return False
    
    async def send_to_repeater(self, request_id: str, tab_name: str = "MCP") -> bool:
        """Send intercepted request to Repeater"""
        request = next((r for r in self._request_queue if r.id == request_id), None)
        if not request:
            return False
        
        result = await self.mcp.create_repeater_tab(
            request.raw_request,
            request.host,
            request.port,
            request.protocol == "https",
            tab_name
        )
        return result.success
    
    async def send_to_intruder(self, request_id: str) -> bool:
        """Send intercepted request to Intruder"""
        request = next((r for r in self._request_queue if r.id == request_id), None)
        if not request:
            return False
        
        result = await self.mcp.send_to_intruder(
            request.raw_request,
            request.host,
            request.port,
            request.protocol == "https"
        )
        return result.success
    
    def add_match_replace_rule(self, match_type: str, match_pattern: str, 
                                replace_with: str, enabled: bool = True) -> str:
        """Add a match and replace rule"""
        rule_id = str(uuid.uuid4())
        self._match_replace_rules.append({
            "id": rule_id,
            "type": match_type,  # request_header, request_body, response_header, response_body
            "match": match_pattern,
            "replace": replace_with,
            "enabled": enabled
        })
        return rule_id
    
    def remove_match_replace_rule(self, rule_id: str):
        """Remove a match and replace rule"""
        self._match_replace_rules = [r for r in self._match_replace_rules if r['id'] != rule_id]
    
    def get_match_replace_rules(self) -> List[Dict]:
        """Get all match and replace rules"""
        return self._match_replace_rules
    
    def apply_match_replace(self, content: str, content_type: str) -> str:
        """Apply matching rules to content"""
        import re
        
        for rule in self._match_replace_rules:
            if not rule['enabled']:
                continue
            if rule['type'] != content_type:
                continue
            
            try:
                content = re.sub(rule['match'], rule['replace'], content)
            except re.error as e:
                logger.error(f"Regex error in rule {rule['id']}: {e}")
        
        return content
    
    def get_pending_requests(self) -> List[InterceptedRequest]:
        """Get all pending intercepted requests"""
        return [r for r in self._request_queue if r.status == "pending"]
    
    def get_pending_responses(self) -> List[InterceptedResponse]:
        """Get all pending intercepted responses"""
        return [r for r in self._response_queue if r.status == "pending"]
    
    async def get_status(self) -> Dict:
        """Get interceptor status"""
        return {
            "enabled": self.intercept_enabled,
            "intercept_requests": self.intercept_requests,
            "intercept_responses": self.intercept_responses,
            "scope_only": self.intercept_scope_only,
            "pending_requests": len(self.get_pending_requests()),
            "pending_responses": len(self.get_pending_responses()),
            "rules_count": len(self._match_replace_rules)
        }


class RequestModifier:
    """
    Utility class for modifying HTTP requests
    """
    
    @staticmethod
    def add_header(request: str, header_name: str, header_value: str) -> str:
        """Add a header to the request"""
        lines = request.split('\n')
        # Insert after first line (request line)
        if len(lines) > 1:
            lines.insert(1, f"{header_name}: {header_value}")
        return '\n'.join(lines)
    
    @staticmethod
    def remove_header(request: str, header_name: str) -> str:
        """Remove a header from the request"""
        lines = request.split('\n')
        lines = [l for l in lines if not l.lower().startswith(f"{header_name.lower()}:")]
        return '\n'.join(lines)
    
    @staticmethod
    def modify_header(request: str, header_name: str, new_value: str) -> str:
        """Modify a header value"""
        lines = request.split('\n')
        for i, line in enumerate(lines):
            if line.lower().startswith(f"{header_name.lower()}:"):
                lines[i] = f"{header_name}: {new_value}"
                break
        return '\n'.join(lines)
    
    @staticmethod
    def replace_body(request: str, new_body: str) -> str:
        """Replace request body"""
        if '\r\n\r\n' in request:
            header_part = request.split('\r\n\r\n')[0]
            return f"{header_part}\r\n\r\n{new_body}"
        elif '\n\n' in request:
            header_part = request.split('\n\n')[0]
            return f"{header_part}\n\n{new_body}"
        return request
    
    @staticmethod
    def modify_parameter(request: str, param_name: str, new_value: str) -> str:
        """Modify a URL or body parameter"""
        import re
        import urllib.parse
        
        # Try URL parameters first
        if f"{param_name}=" in request:
            pattern = rf'({param_name}=)([^&\s]*)'
            request = re.sub(pattern, rf'\1{urllib.parse.quote(new_value)}', request)
        
        # Try JSON body
        if '"' + param_name + '":' in request:
            pattern = rf'("{param_name}":\s*)("[^"]*"|[^,\}}]+)'
            if isinstance(new_value, str):
                request = re.sub(pattern, rf'\1"{new_value}"', request)
            else:
                request = re.sub(pattern, rf'\1{new_value}', request)
        
        return request
    
    @staticmethod
    def change_method(request: str, new_method: str) -> str:
        """Change HTTP method"""
        lines = request.split('\n')
        if lines:
            parts = lines[0].split(' ')
            if len(parts) >= 1:
                parts[0] = new_method.upper()
                lines[0] = ' '.join(parts)
        return '\n'.join(lines)
    
    @staticmethod
    def change_path(request: str, new_path: str) -> str:
        """Change request path"""
        lines = request.split('\n')
        if lines:
            parts = lines[0].split(' ')
            if len(parts) >= 2:
                parts[1] = new_path
                lines[0] = ' '.join(parts)
        return '\n'.join(lines)


class ResponseModifier:
    """
    Utility class for modifying HTTP responses
    """
    
    @staticmethod
    def modify_status(response: str, new_status: int, reason: str = "OK") -> str:
        """Modify response status code"""
        lines = response.split('\n')
        if lines:
            parts = lines[0].split(' ')
            if len(parts) >= 2:
                parts[1] = str(new_status)
                if len(parts) >= 3:
                    parts[2] = reason
                else:
                    parts.append(reason)
                lines[0] = ' '.join(parts)
        return '\n'.join(lines)
    
    @staticmethod
    def add_header(response: str, header_name: str, header_value: str) -> str:
        """Add a header to the response"""
        lines = response.split('\n')
        if len(lines) > 1:
            lines.insert(1, f"{header_name}: {header_value}")
        return '\n'.join(lines)
    
    @staticmethod
    def remove_header(response: str, header_name: str) -> str:
        """Remove a header from the response"""
        lines = response.split('\n')
        lines = [l for l in lines if not l.lower().startswith(f"{header_name.lower()}:")]
        return '\n'.join(lines)
    
    @staticmethod
    def replace_body(response: str, new_body: str) -> str:
        """Replace response body"""
        if '\r\n\r\n' in response:
            header_part = response.split('\r\n\r\n')[0]
            return f"{header_part}\r\n\r\n{new_body}"
        elif '\n\n' in response:
            header_part = response.split('\n\n')[0]
            return f"{header_part}\n\n{new_body}"
        return response
    
    @staticmethod
    def inject_script(response: str, script: str) -> str:
        """Inject JavaScript into HTML response"""
        script_tag = f"<script>{script}</script>"
        
        # Try to inject before </body>
        if '</body>' in response.lower():
            import re
            response = re.sub(
                r'(</body>)',
                f'{script_tag}\\1',
                response,
                flags=re.IGNORECASE
            )
        # Otherwise inject before </html>
        elif '</html>' in response.lower():
            import re
            response = re.sub(
                r'(</html>)',
                f'{script_tag}\\1',
                response,
                flags=re.IGNORECASE
            )
        else:
            # Append to body
            if '\r\n\r\n' in response:
                parts = response.split('\r\n\r\n', 1)
                response = f"{parts[0]}\r\n\r\n{parts[1] if len(parts) > 1 else ''}{script_tag}"
            elif '\n\n' in response:
                parts = response.split('\n\n', 1)
                response = f"{parts[0]}\n\n{parts[1] if len(parts) > 1 else ''}{script_tag}"
        
        return response
