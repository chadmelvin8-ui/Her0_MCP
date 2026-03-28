import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { 
  Shield, 
  Trash2, 
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Filter
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
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

const severityColors = {
  critical: "badge-critical",
  high: "badge-high",
  medium: "badge-medium",
  low: "badge-low",
  info: "badge-info"
};

const severityOrder = ["critical", "high", "medium", "low", "info"];

export default function Findings() {
  const [findings, setFindings] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ session: "all", severity: "all" });
  const [expandedIds, setExpandedIds] = useState(new Set());
  const [deleteTarget, setDeleteTarget] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchFindings();
  }, [filter]);

  const fetchData = async () => {
    try {
      const [findingsRes, sessionsRes] = await Promise.all([
        axios.get(`${API}/findings`),
        axios.get(`${API}/sessions`)
      ]);
      setFindings(findingsRes.data);
      setSessions(sessionsRes.data);
    } catch (error) {
      toast.error("Failed to fetch data");
    } finally {
      setLoading(false);
    }
  };

  const fetchFindings = async () => {
    try {
      let url = `${API}/findings`;
      const params = new URLSearchParams();
      if (filter.session !== "all") params.append("session_id", filter.session);
      if (filter.severity !== "all") params.append("severity", filter.severity);
      if (params.toString()) url += `?${params.toString()}`;
      
      const response = await axios.get(url);
      setFindings(response.data);
    } catch (error) {
      console.error("Failed to fetch findings:", error);
    }
  };

  const deleteFinding = async (id) => {
    try {
      await axios.delete(`${API}/findings/${id}`);
      setFindings(findings.filter(f => f.id !== id));
      toast.success("Finding deleted");
    } catch (error) {
      toast.error("Failed to delete finding");
    }
    setDeleteTarget(null);
  };

  const toggleExpand = (id) => {
    const newExpanded = new Set(expandedIds);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedIds(newExpanded);
  };

  const getSessionName = (sessionId) => {
    const session = sessions.find(s => s.id === sessionId);
    return session?.name || "Unknown Session";
  };

  // Group by severity
  const groupedFindings = severityOrder.reduce((acc, severity) => {
    acc[severity] = findings.filter(f => f.severity === severity);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="findings-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl font-bold text-zinc-100 tracking-tight">
            VULNERABILITY FINDINGS
          </h1>
          <p className="font-mono text-sm text-zinc-500 mt-1">
            {findings.length} findings across {sessions.length} sessions
          </p>
        </div>
        
        {/* Filters */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-zinc-500" />
            <Select 
              value={filter.session} 
              onValueChange={(v) => setFilter({ ...filter, session: v })}
            >
              <SelectTrigger className="w-[180px] input-terminal" data-testid="filter-session">
                <SelectValue placeholder="All Sessions" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-800">
                <SelectItem value="all" className="font-mono text-sm">All Sessions</SelectItem>
                {sessions.map((session) => (
                  <SelectItem 
                    key={session.id} 
                    value={session.id}
                    className="font-mono text-sm"
                  >
                    {session.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <Select 
            value={filter.severity} 
            onValueChange={(v) => setFilter({ ...filter, severity: v })}
          >
            <SelectTrigger className="w-[140px] input-terminal" data-testid="filter-severity">
              <SelectValue placeholder="All Severity" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800">
              <SelectItem value="all" className="font-mono text-sm">All Severity</SelectItem>
              {severityOrder.map((severity) => (
                <SelectItem 
                  key={severity} 
                  value={severity}
                  className="font-mono text-sm capitalize"
                >
                  {severity}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Findings List */}
      {findings.length > 0 ? (
        <ScrollArea className="h-[calc(100vh-14rem)]">
          <div className="space-y-3">
            {findings.map((finding) => (
              <Collapsible 
                key={finding.id}
                open={expandedIds.has(finding.id)}
                onOpenChange={() => toggleExpand(finding.id)}
              >
                <Card className="card-default overflow-hidden" data-testid={`finding-${finding.id}`}>
                  <CollapsibleTrigger className="w-full text-left">
                    <div className="p-4 flex items-start gap-4 hover:bg-zinc-800/50 transition-colors">
                      <div className="pt-0.5">
                        {expandedIds.has(finding.id) ? (
                          <ChevronDown className="w-4 h-4 text-zinc-500" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-zinc-500" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge className={`${severityColors[finding.severity]} font-mono text-[10px] uppercase px-2`}>
                            {finding.severity}
                          </Badge>
                          <span className="font-mono text-xs text-zinc-500">
                            {finding.vulnerability_type}
                          </span>
                          <span className="font-mono text-xs text-zinc-600">
                            • {getSessionName(finding.session_id)}
                          </span>
                        </div>
                        <h3 className="font-mono text-sm text-zinc-100">
                          {finding.title}
                        </h3>
                        <p className="font-mono text-xs text-zinc-500 mt-1 line-clamp-2">
                          {finding.description}
                        </p>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-red-500 hover:text-red-400 hover:bg-red-500/10"
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeleteTarget(finding);
                        }}
                        data-testid={`delete-finding-${finding.id}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CollapsibleTrigger>
                  
                  <CollapsibleContent>
                    <div className="px-4 pb-4 pt-0 space-y-4 border-t border-zinc-800">
                      {/* Description */}
                      <div className="pt-4">
                        <h4 className="font-mono text-xs text-zinc-500 uppercase tracking-wider mb-2">
                          Description
                        </h4>
                        <p className="font-mono text-sm text-zinc-300">
                          {finding.description}
                        </p>
                      </div>
                      
                      {/* Evidence */}
                      <div>
                        <h4 className="font-mono text-xs text-zinc-500 uppercase tracking-wider mb-2">
                          Evidence
                        </h4>
                        <div className="code-block text-emerald-400">
                          {finding.evidence}
                        </div>
                      </div>
                      
                      {/* Request Data */}
                      {finding.request_data && (
                        <div>
                          <h4 className="font-mono text-xs text-zinc-500 uppercase tracking-wider mb-2">
                            Request
                          </h4>
                          <div className="code-block text-zinc-300">
                            {JSON.stringify(finding.request_data, null, 2)}
                          </div>
                        </div>
                      )}
                      
                      {/* Recommendations */}
                      {finding.recommendations?.length > 0 && (
                        <div>
                          <h4 className="font-mono text-xs text-zinc-500 uppercase tracking-wider mb-2">
                            Recommendations
                          </h4>
                          <ul className="space-y-1">
                            {finding.recommendations.map((rec, idx) => (
                              <li key={idx} className="font-mono text-sm text-zinc-300 flex items-start gap-2">
                                <span className="text-emerald-500">•</span>
                                {rec}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </CollapsibleContent>
                </Card>
              </Collapsible>
            ))}
          </div>
        </ScrollArea>
      ) : (
        <Card className="card-terminal">
          <div className="scanlines" />
          <CardContent className="p-12 text-center relative z-20">
            <Shield className="w-16 h-16 text-emerald-500/30 mx-auto mb-4" />
            <h3 className="font-mono text-lg text-zinc-200 mb-2">No Findings Yet</h3>
            <p className="font-mono text-sm text-zinc-500">
              Start a hunting session to discover vulnerabilities
            </p>
          </CardContent>
        </Card>
      )}

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <AlertDialogContent className="bg-zinc-900 border-zinc-800">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-mono text-zinc-100">
              Delete Finding?
            </AlertDialogTitle>
            <AlertDialogDescription className="font-mono text-sm text-zinc-400">
              This will permanently delete this vulnerability finding.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="btn-outline">Cancel</AlertDialogCancel>
            <AlertDialogAction 
              className="btn-danger"
              onClick={() => deleteFinding(deleteTarget?.id)}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
