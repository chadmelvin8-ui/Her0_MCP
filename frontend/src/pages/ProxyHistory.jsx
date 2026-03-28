import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { 
  History, 
  ChevronDown,
  ChevronRight,
  Eye,
  AlertCircle,
  Flag
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const methodColors = {
  GET: "method-get",
  POST: "method-post",
  PUT: "method-put",
  DELETE: "method-delete",
  PATCH: "method-patch",
  OPTIONS: "text-zinc-500",
  HEAD: "text-zinc-500",
};

const statusColors = {
  2: "text-emerald-500",
  3: "text-blue-500",
  4: "text-amber-500",
  5: "text-red-500",
};

export default function ProxyHistory() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(sessionId || "");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    if (selectedSession) {
      fetchHistory();
      navigate(`/proxy-history/${selectedSession}`, { replace: true });
    }
  }, [selectedSession]);

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`${API}/sessions`);
      setSessions(response.data);
      if (!selectedSession && response.data.length > 0) {
        setSelectedSession(response.data[0].id);
      }
    } catch (error) {
      console.error("Failed to fetch sessions:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    if (!selectedSession) return;
    try {
      const response = await axios.get(`${API}/proxy-history/${selectedSession}`);
      setHistory(response.data);
    } catch (error) {
      console.error("Failed to fetch history:", error);
    }
  };

  const getStatusColor = (status) => {
    if (!status) return "text-zinc-500";
    const firstDigit = Math.floor(status / 100);
    return statusColors[firstDigit] || "text-zinc-500";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="spinner" />
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="flex items-center justify-center h-full" data-testid="proxy-no-sessions">
        <Card className="card-terminal max-w-md">
          <div className="scanlines" />
          <CardContent className="p-8 text-center relative z-20">
            <History className="w-12 h-12 text-emerald-500/50 mx-auto mb-4" />
            <h3 className="font-mono text-lg text-zinc-200 mb-2">No Sessions Available</h3>
            <p className="font-mono text-sm text-zinc-500">
              Create a session first to view proxy history
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="proxy-history-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl font-bold text-zinc-100 tracking-tight">
            PROXY HISTORY
          </h1>
          <p className="font-mono text-sm text-zinc-500 mt-1">
            {history.length} requests captured
          </p>
        </div>
        
        <Select value={selectedSession} onValueChange={setSelectedSession}>
          <SelectTrigger className="w-[250px] input-terminal" data-testid="session-selector">
            <SelectValue placeholder="Select session" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-900 border-zinc-800">
            {sessions.map((session) => (
              <SelectItem 
                key={session.id} 
                value={session.id}
                className="font-mono text-sm text-zinc-300"
              >
                {session.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* History Table */}
      {history.length > 0 ? (
        <Card className="card-default overflow-hidden">
          <div className="overflow-x-auto">
            <table className="table-terminal">
              <thead>
                <tr>
                  <th className="w-12">#</th>
                  <th className="w-20">Method</th>
                  <th>URL</th>
                  <th className="w-20">Status</th>
                  <th className="w-24">Analyzed</th>
                  <th className="w-20">Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item, index) => (
                  <tr 
                    key={item.id} 
                    className="cursor-pointer"
                    onClick={() => setSelectedItem(item)}
                    data-testid={`history-row-${index}`}
                  >
                    <td className="text-zinc-500">{index + 1}</td>
                    <td>
                      <span className={`font-mono font-semibold ${methodColors[item.method] || "text-zinc-400"}`}>
                        {item.method}
                      </span>
                    </td>
                    <td className="max-w-[400px]">
                      <div className="truncate text-zinc-300" title={item.url}>
                        {item.url}
                      </div>
                    </td>
                    <td>
                      <span className={`font-mono ${getStatusColor(item.status_code)}`}>
                        {item.status_code || "-"}
                      </span>
                    </td>
                    <td>
                      {item.analyzed ? (
                        <Badge className="badge-info font-mono text-[10px]">ANALYZED</Badge>
                      ) : (
                        <Badge className="bg-zinc-800 text-zinc-500 border-zinc-700 font-mono text-[10px]">
                          PENDING
                        </Badge>
                      )}
                    </td>
                    <td>
                      <button 
                        className="p-1.5 hover:bg-zinc-800 transition-colors"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedItem(item);
                        }}
                      >
                        <Eye className="w-4 h-4 text-zinc-500 hover:text-zinc-300" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <Card className="card-terminal">
          <div className="scanlines" />
          <CardContent className="p-12 text-center relative z-20">
            <History className="w-16 h-16 text-emerald-500/30 mx-auto mb-4" />
            <h3 className="font-mono text-lg text-zinc-200 mb-2">No Proxy History</h3>
            <p className="font-mono text-sm text-zinc-500">
              Capture traffic with Burp Suite or add mock data to see history
            </p>
          </CardContent>
        </Card>
      )}

      {/* Request Detail Dialog */}
      <Dialog open={!!selectedItem} onOpenChange={() => setSelectedItem(null)}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-4xl max-h-[80vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="font-mono text-zinc-100 flex items-center gap-3">
              <span className={`${methodColors[selectedItem?.method] || "text-zinc-400"}`}>
                {selectedItem?.method}
              </span>
              <span className="text-zinc-500 truncate text-sm font-normal">
                {selectedItem?.url}
              </span>
            </DialogTitle>
          </DialogHeader>
          
          <Tabs defaultValue="request" className="flex-1 overflow-hidden">
            <TabsList className="bg-zinc-800 border border-zinc-700">
              <TabsTrigger 
                value="request" 
                className="font-mono text-xs data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-500"
              >
                Request
              </TabsTrigger>
              <TabsTrigger 
                value="response"
                className="font-mono text-xs data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-500"
              >
                Response
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="request" className="mt-4 overflow-hidden">
              <ScrollArea className="h-[400px]">
                <div className="space-y-4">
                  <div>
                    <h4 className="font-mono text-xs text-zinc-500 uppercase tracking-wider mb-2">
                      Headers
                    </h4>
                    <div className="code-block">
                      {selectedItem?.request_headers && Object.keys(selectedItem.request_headers).length > 0 ? (
                        Object.entries(selectedItem.request_headers).map(([key, value]) => (
                          <div key={key} className="text-zinc-300">
                            <span className="text-emerald-500">{key}</span>: {value}
                          </div>
                        ))
                      ) : (
                        <span className="text-zinc-500">No headers</span>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-mono text-xs text-zinc-500 uppercase tracking-wider mb-2">
                      Body
                    </h4>
                    <div className="code-block text-zinc-300">
                      {selectedItem?.request_body || <span className="text-zinc-500">No body</span>}
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </TabsContent>
            
            <TabsContent value="response" className="mt-4 overflow-hidden">
              <ScrollArea className="h-[400px]">
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <span className="font-mono text-xs text-zinc-500">Status:</span>
                    <span className={`font-mono font-semibold ${getStatusColor(selectedItem?.status_code)}`}>
                      {selectedItem?.status_code || "N/A"}
                    </span>
                  </div>
                  
                  <div>
                    <h4 className="font-mono text-xs text-zinc-500 uppercase tracking-wider mb-2">
                      Headers
                    </h4>
                    <div className="code-block">
                      {selectedItem?.response_headers && Object.keys(selectedItem.response_headers).length > 0 ? (
                        Object.entries(selectedItem.response_headers).map(([key, value]) => (
                          <div key={key} className="text-zinc-300">
                            <span className="text-emerald-500">{key}</span>: {value}
                          </div>
                        ))
                      ) : (
                        <span className="text-zinc-500">No headers</span>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-mono text-xs text-zinc-500 uppercase tracking-wider mb-2">
                      Body
                    </h4>
                    <div className="code-block text-zinc-300">
                      {selectedItem?.response_body || <span className="text-zinc-500">No body</span>}
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>
    </div>
  );
}
