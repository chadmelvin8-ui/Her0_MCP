import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { 
  Plus, 
  Trash2, 
  Play, 
  Square, 
  MessageSquare,
  History,
  FileText,
  Target,
  Clock,
  Shield,
  Upload,
  Zap
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
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

const statusColors = {
  idle: "bg-zinc-500/10 text-zinc-400 border-zinc-500/30",
  hunting: "bg-amber-500/10 text-amber-500 border-amber-500/30",
  analyzing: "bg-blue-500/10 text-blue-500 border-blue-500/30",
  completed: "bg-emerald-500/10 text-emerald-500 border-emerald-500/30",
};

export default function Sessions() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showImport, setShowImport] = useState(null); // session ID for import
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [newSession, setNewSession] = useState({ name: "", target_url: "" });
  const [creating, setCreating] = useState(false);
  const [importing, setImporting] = useState(false);
  const [showHuntAuth, setShowHuntAuth] = useState(null); // session for hunt authorization

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`${API}/sessions`);
      setSessions(response.data);
    } catch (error) {
      toast.error("Failed to fetch sessions");
    } finally {
      setLoading(false);
    }
  };

  const createSession = async () => {
    if (!newSession.name.trim()) {
      toast.error("Session name is required");
      return;
    }
    
    setCreating(true);
    try {
      const response = await axios.post(`${API}/sessions`, newSession);
      setSessions([response.data, ...sessions]);
      setShowCreate(false);
      setNewSession({ name: "", target_url: "" });
      toast.success("Session created successfully");
    } catch (error) {
      toast.error("Failed to create session");
    } finally {
      setCreating(false);
    }
  };

  const deleteSession = async (id) => {
    try {
      await axios.delete(`${API}/sessions/${id}`);
      setSessions(sessions.filter(s => s.id !== id));
      toast.success("Session deleted");
    } catch (error) {
      toast.error("Failed to delete session");
    }
    setDeleteTarget(null);
  };

  const startHunt = async (sessionId, strategy = "passive", authorized = false) => {
    try {
      await axios.post(`${API}/hunt/start/${sessionId}`, {
        strategy,
        authorized,
        target_scope: []
      });
      toast.success(`Autonomous hunting started (${strategy} mode)`);
      fetchSessions();
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("Active hunting requires authorization");
      } else {
        toast.error("Failed to start hunting");
      }
    }
    setShowHuntAuth(null);
  };

  const stopHunt = async (sessionId) => {
    try {
      await axios.post(`${API}/hunt/stop/${sessionId}`);
      toast.success("Hunting stopped");
      fetchSessions();
    } catch (error) {
      toast.error("Failed to stop hunting");
    }
  };

  const importBurpFile = async (sessionId, file) => {
    setImporting(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(
        `${API}/import/burp-file?session_id=${sessionId}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      
      toast.success(`Imported ${response.data.imported} requests`);
      fetchSessions();
    } catch (error) {
      toast.error("Failed to import file. Ensure it's a valid Burp export (.xml or .json)");
    } finally {
      setImporting(false);
      setShowImport(null);
    }
  };

  const generateMockData = async (sessionId) => {
    try {
      await axios.post(`${API}/mock/proxy-data/${sessionId}`);
      toast.success("Mock proxy data generated");
      fetchSessions();
    } catch (error) {
      toast.error("Failed to generate mock data");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="sessions-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl font-bold text-zinc-100 tracking-tight">
            HUNTING SESSIONS
          </h1>
          <p className="font-mono text-sm text-zinc-500 mt-1">
            Manage your penetration testing sessions
          </p>
        </div>
        <Button 
          className="btn-primary px-6 py-2" 
          onClick={() => setShowCreate(true)}
          data-testid="create-session-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Session
        </Button>
      </div>

      {/* Sessions Grid */}
      {sessions.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sessions.map((session) => (
            <Card key={session.id} className="card-default hover:border-zinc-700 transition-colors" data-testid={`session-${session.id}`}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <CardTitle className="font-mono text-base text-zinc-100 truncate">
                      {session.name}
                    </CardTitle>
                    {session.target_url && (
                      <p className="font-mono text-xs text-zinc-500 truncate mt-1">
                        {session.target_url}
                      </p>
                    )}
                  </div>
                  <Badge className={`${statusColors[session.status]} font-mono text-[10px] uppercase`}>
                    {session.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Stats */}
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-zinc-500" />
                    <span className="font-mono text-zinc-400">{session.findings_count}</span>
                    <span className="font-mono text-xs text-zinc-600">findings</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <History className="w-3.5 h-3.5 text-zinc-500" />
                    <span className="font-mono text-zinc-400">{session.requests_analyzed}</span>
                    <span className="font-mono text-xs text-zinc-600">requests</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  {session.status === "hunting" ? (
                    <Button 
                      size="sm" 
                      className="btn-danger flex-1"
                      onClick={() => stopHunt(session.id)}
                      data-testid={`stop-hunt-${session.id}`}
                    >
                      <Square className="w-3 h-3 mr-1" />
                      Stop
                    </Button>
                  ) : (
                    <Button 
                      size="sm" 
                      className="btn-primary flex-1"
                      onClick={() => setShowHuntAuth(session)}
                      data-testid={`start-hunt-${session.id}`}
                    >
                      <Zap className="w-3 h-3 mr-1" />
                      Hunt
                    </Button>
                  )}
                  <Button 
                    size="sm" 
                    variant="outline"
                    className="btn-outline"
                    onClick={() => navigate(`/chat/${session.id}`)}
                    data-testid={`chat-${session.id}`}
                  >
                    <MessageSquare className="w-3 h-3" />
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline"
                    className="btn-outline"
                    onClick={() => navigate(`/proxy-history/${session.id}`)}
                    data-testid={`history-${session.id}`}
                  >
                    <History className="w-3 h-3" />
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline"
                    className="btn-outline"
                    onClick={() => navigate(`/reports/${session.id}`)}
                    data-testid={`report-${session.id}`}
                  >
                    <FileText className="w-3 h-3" />
                  </Button>
                </div>

                {/* Additional Actions */}
                <div className="flex items-center justify-between pt-2 border-t border-zinc-800">
                  <div className="flex items-center gap-1">
                    <Button 
                      size="sm" 
                      variant="ghost"
                      className="text-xs text-zinc-500 hover:text-zinc-300 px-2"
                      onClick={() => setShowImport(session.id)}
                      data-testid={`import-${session.id}`}
                    >
                      <Upload className="w-3 h-3 mr-1" />
                      Import
                    </Button>
                    <Button 
                      size="sm" 
                      variant="ghost"
                      className="text-xs text-zinc-500 hover:text-zinc-300 px-2"
                      onClick={() => generateMockData(session.id)}
                      data-testid={`mock-data-${session.id}`}
                    >
                      <Target className="w-3 h-3 mr-1" />
                      Mock
                    </Button>
                  </div>
                  <Button 
                    size="sm" 
                    variant="ghost"
                    className="text-xs text-red-500 hover:text-red-400 hover:bg-red-500/10 px-2"
                    onClick={() => setDeleteTarget(session)}
                    data-testid={`delete-${session.id}`}
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>

                {/* Timestamp */}
                <div className="flex items-center gap-1 text-xs text-zinc-600">
                  <Clock className="w-3 h-3" />
                  <span className="font-mono">
                    {new Date(session.created_at).toLocaleDateString()}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="card-terminal">
          <div className="scanlines" />
          <CardContent className="p-12 text-center relative z-20">
            <Target className="w-16 h-16 text-emerald-500/30 mx-auto mb-4" />
            <h3 className="font-mono text-lg text-zinc-200 mb-2">No Sessions Yet</h3>
            <p className="font-mono text-sm text-zinc-500 mb-6">
              Create your first hunting session to begin vulnerability assessment
            </p>
            <Button 
              className="btn-primary px-8"
              onClick={() => setShowCreate(true)}
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Session
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Create Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="bg-zinc-900 border-zinc-800">
          <DialogHeader>
            <DialogTitle className="font-mono text-lg text-zinc-100">
              Create New Session
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="font-mono text-xs text-zinc-400 uppercase tracking-wider">
                Session Name
              </label>
              <Input
                className="input-terminal"
                placeholder="e.g., Target API Assessment"
                value={newSession.name}
                onChange={(e) => setNewSession({ ...newSession, name: e.target.value })}
                data-testid="session-name-input"
              />
            </div>
            <div className="space-y-2">
              <label className="font-mono text-xs text-zinc-400 uppercase tracking-wider">
                Target URL (Optional)
              </label>
              <Input
                className="input-terminal"
                placeholder="https://target.com"
                value={newSession.target_url}
                onChange={(e) => setNewSession({ ...newSession, target_url: e.target.value })}
                data-testid="session-url-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              className="btn-outline"
              onClick={() => setShowCreate(false)}
            >
              Cancel
            </Button>
            <Button 
              className="btn-primary"
              onClick={createSession}
              disabled={creating}
              data-testid="confirm-create-session"
            >
              {creating ? <div className="spinner mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <AlertDialogContent className="bg-zinc-900 border-zinc-800">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-mono text-zinc-100">
              Delete Session?
            </AlertDialogTitle>
            <AlertDialogDescription className="font-mono text-sm text-zinc-400">
              This will permanently delete "{deleteTarget?.name}" and all associated data including findings, chat history, and proxy history.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="btn-outline">Cancel</AlertDialogCancel>
            <AlertDialogAction 
              className="btn-danger"
              onClick={() => deleteSession(deleteTarget?.id)}
              data-testid="confirm-delete"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Import Burp File Dialog */}
      <Dialog open={!!showImport} onOpenChange={() => setShowImport(null)}>
        <DialogContent className="bg-zinc-900 border-zinc-800">
          <DialogHeader>
            <DialogTitle className="font-mono text-lg text-zinc-100">
              Import Burp Suite Export
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p className="font-mono text-sm text-zinc-400">
              Upload a Burp Suite export file (.xml or .json) to import proxy history for analysis.
            </p>
            <div className="border-2 border-dashed border-zinc-700 p-6 text-center">
              <Upload className="w-8 h-8 text-zinc-500 mx-auto mb-2" />
              <input
                type="file"
                accept=".xml,.json"
                onChange={(e) => {
                  if (e.target.files[0]) {
                    importBurpFile(showImport, e.target.files[0]);
                  }
                }}
                className="hidden"
                id="burp-file-input"
              />
              <label 
                htmlFor="burp-file-input"
                className="font-mono text-sm text-emerald-500 cursor-pointer hover:underline"
              >
                {importing ? "Importing..." : "Click to select file"}
              </label>
              <p className="font-mono text-xs text-zinc-600 mt-2">
                Supports Burp XML and JSON exports
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              className="btn-outline"
              onClick={() => setShowImport(null)}
              disabled={importing}
            >
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Hunt Authorization Dialog */}
      <Dialog open={!!showHuntAuth} onOpenChange={() => setShowHuntAuth(null)}>
        <DialogContent className="bg-zinc-900 border-zinc-800">
          <DialogHeader>
            <DialogTitle className="font-mono text-lg text-zinc-100">
              Start Vulnerability Hunt
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p className="font-mono text-sm text-zinc-400">
              Choose hunting strategy for "{showHuntAuth?.name}":
            </p>
            
            <div className="space-y-3">
              <div 
                className="p-3 border border-zinc-700 hover:border-emerald-500/50 cursor-pointer transition-colors"
                onClick={() => startHunt(showHuntAuth?.id, "passive", false)}
              >
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-2 h-2 bg-emerald-500" />
                  <span className="font-mono text-sm text-zinc-200">Passive Analysis</span>
                </div>
                <p className="font-mono text-xs text-zinc-500 ml-4">
                  Analyze existing traffic without sending requests. Safe for any target.
                </p>
              </div>
              
              <div 
                className="p-3 border border-zinc-700 hover:border-amber-500/50 cursor-pointer transition-colors"
                onClick={() => startHunt(showHuntAuth?.id, "active_safe", true)}
              >
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-2 h-2 bg-amber-500" />
                  <span className="font-mono text-sm text-zinc-200">Active (Safe)</span>
                </div>
                <p className="font-mono text-xs text-zinc-500 ml-4">
                  Send non-destructive test requests. Requires authorization.
                </p>
              </div>
              
              <div 
                className="p-3 border border-zinc-700 hover:border-red-500/50 cursor-pointer transition-colors"
                onClick={() => startHunt(showHuntAuth?.id, "active_full", true)}
              >
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-2 h-2 bg-red-500" />
                  <span className="font-mono text-sm text-zinc-200">Active (Full)</span>
                </div>
                <p className="font-mono text-xs text-zinc-500 ml-4">
                  Full autonomous testing with payloads. Only for authorized targets!
                </p>
              </div>
            </div>

            <div className="bg-amber-500/10 border border-amber-500/30 p-3 mt-4">
              <p className="font-mono text-xs text-amber-500">
                ⚠️ Active modes send real requests. Only use on targets you own or have explicit permission to test.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              className="btn-outline"
              onClick={() => setShowHuntAuth(null)}
            >
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
