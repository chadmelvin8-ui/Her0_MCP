import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { 
  Radio,
  Play,
  Pause,
  Send,
  Trash2,
  Edit3,
  ChevronDown,
  ChevronRight,
  Copy,
  CornerDownRight,
  Crosshair,
  AlertTriangle
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const methodColors = {
  GET: "text-emerald-500",
  POST: "text-blue-500",
  PUT: "text-amber-500",
  DELETE: "text-red-500",
  PATCH: "text-purple-500",
};

export default function Interceptor() {
  const [interceptEnabled, setInterceptEnabled] = useState(false);
  const [interceptedRequests, setInterceptedRequests] = useState([]);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [editedContent, setEditedContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [showAuthWarning, setShowAuthWarning] = useState(false);
  const [burpConnected, setBurpConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    fetchStatus();
    connectWebSocket();
    
    const interval = setInterval(fetchInterceptedRequests, 2000);
    return () => {
      clearInterval(interval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const wsUrl = process.env.REACT_APP_BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    try {
      wsRef.current = new WebSocket(`${wsUrl}/ws`);
      
      wsRef.current.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === "intercept_status") {
          setInterceptEnabled(message.data.enabled);
        } else if (message.type === "request_processed") {
          fetchInterceptedRequests();
        }
      };
      
      wsRef.current.onerror = () => {
        console.log("WebSocket connection failed, using polling");
      };
    } catch (e) {
      console.log("WebSocket not available");
    }
  };

  const fetchStatus = async () => {
    try {
      const [statusRes, burpRes] = await Promise.all([
        axios.get(`${API}/interceptor/status`),
        axios.get(`${API}/burp/status`)
      ]);
      setInterceptEnabled(statusRes.data.enabled);
      setBurpConnected(burpRes.data.connected);
    } catch (error) {
      console.error("Failed to fetch status:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchInterceptedRequests = async () => {
    try {
      const response = await axios.get(`${API}/interceptor/requests`);
      setInterceptedRequests(response.data);
    } catch (error) {
      // Silent fail for polling
    }
  };

  const toggleIntercept = async () => {
    if (!burpConnected) {
      toast.error("Burp Suite MCP not connected. Please start Burp with MCP extension.");
      return;
    }
    
    try {
      const response = await axios.post(`${API}/interceptor/toggle`);
      setInterceptEnabled(response.data.enabled);
      toast.success(response.data.enabled ? "Intercept enabled" : "Intercept disabled");
    } catch (error) {
      toast.error("Failed to toggle intercept");
    }
  };

  const handleSelectRequest = (request) => {
    setSelectedRequest(request);
    setEditedContent(request.raw_request || "");
  };

  const forwardRequest = async (modified = false) => {
    if (!selectedRequest) return;
    
    try {
      await axios.post(`${API}/interceptor/request/${selectedRequest.id}/forward`, {
        action: modified ? "forward_modified" : "forward",
        modified_content: modified ? editedContent : null
      });
      toast.success(modified ? "Request forwarded (modified)" : "Request forwarded");
      setSelectedRequest(null);
      fetchInterceptedRequests();
    } catch (error) {
      toast.error("Failed to forward request");
    }
  };

  const dropRequest = async () => {
    if (!selectedRequest) return;
    
    try {
      await axios.post(`${API}/interceptor/request/${selectedRequest.id}/forward`, {
        action: "drop"
      });
      toast.success("Request dropped");
      setSelectedRequest(null);
      fetchInterceptedRequests();
    } catch (error) {
      toast.error("Failed to drop request");
    }
  };

  const sendToRepeater = async () => {
    if (!selectedRequest) return;
    
    try {
      await axios.post(`${API}/interceptor/request/${selectedRequest.id}/repeater?tab_name=MCP`);
      toast.success("Sent to Repeater");
    } catch (error) {
      toast.error("Failed to send to Repeater");
    }
  };

  const sendToIntruder = async () => {
    if (!selectedRequest) return;
    
    try {
      await axios.post(`${API}/interceptor/request/${selectedRequest.id}/intruder`);
      toast.success("Sent to Intruder");
    } catch (error) {
      toast.error("Failed to send to Intruder");
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(editedContent);
    toast.success("Copied to clipboard");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="interceptor-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl font-bold text-zinc-100 tracking-tight">
            PROXY INTERCEPTOR
          </h1>
          <p className="font-mono text-sm text-zinc-500 mt-1">
            Real-time request interception and modification
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 ${burpConnected ? 'bg-emerald-500' : 'bg-red-500'}`} />
            <span className="font-mono text-xs text-zinc-500">
              {burpConnected ? 'Burp Connected' : 'Burp Disconnected'}
            </span>
          </div>
          
          {/* Intercept Toggle */}
          <Button
            className={interceptEnabled ? "btn-danger" : "btn-primary"}
            onClick={toggleIntercept}
            data-testid="toggle-intercept-btn"
          >
            {interceptEnabled ? (
              <>
                <Pause className="w-4 h-4 mr-2" />
                Intercept ON
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Intercept OFF
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Warning Banner */}
      {!burpConnected && (
        <Card className="bg-amber-500/10 border-amber-500/30">
          <CardContent className="p-4 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0" />
            <div>
              <p className="font-mono text-sm text-amber-500 font-medium">
                Burp Suite MCP Not Connected
              </p>
              <p className="font-mono text-xs text-amber-500/70 mt-1">
                Start Burp Suite with the MCP Server extension enabled on port 9876, then refresh.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-18rem)]">
        {/* Intercepted Requests List */}
        <Card className="card-default flex flex-col">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <CardTitle className="font-mono text-sm uppercase tracking-wider text-zinc-400 flex items-center gap-2">
              <Radio className={`w-4 h-4 ${interceptEnabled ? 'text-red-500 animate-pulse' : 'text-zinc-500'}`} />
              Intercepted Requests
              {interceptedRequests.length > 0 && (
                <Badge className="badge-high ml-2">{interceptedRequests.length}</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              {interceptedRequests.length > 0 ? (
                <div className="space-y-2">
                  {interceptedRequests.map((request, index) => (
                    <div
                      key={request.id}
                      className={`p-3 border cursor-pointer transition-all ${
                        selectedRequest?.id === request.id
                          ? 'bg-emerald-500/10 border-emerald-500/30'
                          : 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700'
                      }`}
                      onClick={() => handleSelectRequest(request)}
                      data-testid={`intercepted-request-${index}`}
                    >
                      <div className="flex items-center gap-3">
                        <span className={`font-mono font-bold ${methodColors[request.method] || 'text-zinc-400'}`}>
                          {request.method}
                        </span>
                        <span className="font-mono text-sm text-zinc-300 truncate flex-1">
                          {request.url}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="font-mono text-xs text-zinc-600">{request.host}</span>
                        <span className="font-mono text-xs text-zinc-700">
                          {new Date(request.intercepted_at).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center py-12">
                  <Crosshair className="w-12 h-12 text-zinc-700 mb-4" />
                  <p className="font-mono text-sm text-zinc-500">
                    {interceptEnabled ? "Waiting for requests..." : "Enable intercept to capture requests"}
                  </p>
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Request Editor */}
        <Card className="card-terminal flex flex-col">
          <div className="scanlines" />
          <CardHeader className="pb-3 relative z-20">
            <CardTitle className="font-mono text-sm uppercase tracking-wider text-emerald-500 flex items-center gap-2">
              <Edit3 className="w-4 h-4" />
              Request Editor
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col overflow-hidden relative z-20">
            {selectedRequest ? (
              <>
                {/* Request Info */}
                <div className="flex items-center gap-2 mb-3">
                  <Badge className={`font-mono text-xs ${methodColors[selectedRequest.method]?.replace('text-', 'bg-').replace('500', '500/20')} border-current`}>
                    {selectedRequest.method}
                  </Badge>
                  <span className="font-mono text-xs text-zinc-400 truncate">
                    {selectedRequest.host}
                  </span>
                </div>

                {/* Editor */}
                <Textarea
                  className="flex-1 font-mono text-sm bg-[#050505] border-emerald-500/30 text-emerald-400 resize-none min-h-[300px]"
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  placeholder="Raw HTTP request..."
                  data-testid="request-editor"
                />

                {/* Actions */}
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-emerald-500/20">
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      className="btn-primary"
                      onClick={() => forwardRequest(false)}
                      data-testid="forward-btn"
                    >
                      <Send className="w-3 h-3 mr-1" />
                      Forward
                    </Button>
                    <Button
                      size="sm"
                      className="btn-outline"
                      onClick={() => forwardRequest(true)}
                      disabled={editedContent === selectedRequest.raw_request}
                      data-testid="forward-modified-btn"
                    >
                      <Edit3 className="w-3 h-3 mr-1" />
                      Forward Modified
                    </Button>
                    <Button
                      size="sm"
                      className="btn-danger"
                      onClick={dropRequest}
                      data-testid="drop-btn"
                    >
                      <Trash2 className="w-3 h-3 mr-1" />
                      Drop
                    </Button>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-zinc-500 hover:text-zinc-300"
                      onClick={copyToClipboard}
                    >
                      <Copy className="w-3 h-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-zinc-500 hover:text-zinc-300"
                      onClick={sendToRepeater}
                      title="Send to Repeater"
                    >
                      <CornerDownRight className="w-3 h-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-zinc-500 hover:text-zinc-300"
                      onClick={sendToIntruder}
                      title="Send to Intruder"
                    >
                      <Crosshair className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Edit3 className="w-12 h-12 text-emerald-500/30 mb-4" />
                <p className="font-mono text-sm text-zinc-500">
                  Select an intercepted request to view/edit
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Tips */}
      <Card className="card-default">
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center flex-shrink-0">
                <span className="font-mono text-xs text-emerald-500">1</span>
              </div>
              <div>
                <p className="font-mono text-xs text-zinc-400">Forward</p>
                <p className="font-mono text-xs text-zinc-600">Send request unchanged</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-amber-500/10 border border-amber-500/30 flex items-center justify-center flex-shrink-0">
                <span className="font-mono text-xs text-amber-500">2</span>
              </div>
              <div>
                <p className="font-mono text-xs text-zinc-400">Forward Modified</p>
                <p className="font-mono text-xs text-zinc-600">Send with your edits</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-red-500/10 border border-red-500/30 flex items-center justify-center flex-shrink-0">
                <span className="font-mono text-xs text-red-500">3</span>
              </div>
              <div>
                <p className="font-mono text-xs text-zinc-400">Drop</p>
                <p className="font-mono text-xs text-zinc-600">Block the request</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
