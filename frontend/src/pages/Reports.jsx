import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { 
  FileText, 
  Download,
  Printer,
  Shield,
  AlertTriangle,
  Calendar,
  Target
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

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const severityColors = {
  critical: "badge-critical",
  high: "badge-high",
  medium: "badge-medium",
  low: "badge-low",
  info: "badge-info"
};

export default function Reports() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(sessionId || "");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    if (selectedSession) {
      fetchReport();
      navigate(`/reports/${selectedSession}`, { replace: true });
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

  const fetchReport = async () => {
    if (!selectedSession) return;
    setLoading(true);
    try {
      const response = await axios.get(`${API}/reports/${selectedSession}`);
      setReport(response.data);
    } catch (error) {
      console.error("Failed to fetch report:", error);
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  const exportReport = () => {
    if (!report) return;
    const dataStr = JSON.stringify(report, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `security-report-${selectedSession.slice(0, 8)}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    toast.success("Report exported");
  };

  if (loading && sessions.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="spinner" />
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="flex items-center justify-center h-full" data-testid="reports-no-sessions">
        <Card className="card-terminal max-w-md">
          <div className="scanlines" />
          <CardContent className="p-8 text-center relative z-20">
            <FileText className="w-12 h-12 text-emerald-500/50 mx-auto mb-4" />
            <h3 className="font-mono text-lg text-zinc-200 mb-2">No Sessions Available</h3>
            <p className="font-mono text-sm text-zinc-500">
              Create a session and find some vulnerabilities first
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="reports-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl font-bold text-zinc-100 tracking-tight">
            SECURITY REPORT
          </h1>
          <p className="font-mono text-sm text-zinc-500 mt-1">
            Professional vulnerability assessment report
          </p>
        </div>
        
        <div className="flex items-center gap-3">
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
          
          <Button 
            variant="outline" 
            className="btn-outline"
            onClick={exportReport}
            disabled={!report}
            data-testid="export-report-btn"
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="spinner" />
        </div>
      ) : report ? (
        <ScrollArea className="h-[calc(100vh-14rem)]">
          {/* Report Header */}
          <Card className="card-terminal mb-6">
            <div className="scanlines" />
            <CardContent className="p-6 relative z-20">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="font-mono text-xl text-emerald-500 mb-2">
                    {report.session?.name || "Security Assessment"}
                  </h2>
                  {report.session?.target_url && (
                    <p className="font-mono text-sm text-zinc-400">
                      Target: {report.session.target_url}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <div className="flex items-center gap-2 text-zinc-500 mb-1">
                    <Calendar className="w-4 h-4" />
                    <span className="font-mono text-xs">
                      {new Date(report.generated_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="font-mono text-xs text-zinc-600">
                    MCP'Arsonist AI Report
                  </p>
                </div>
              </div>

              {/* Summary Stats */}
              <div className="grid grid-cols-5 gap-4">
                <SummaryCard 
                  label="Total" 
                  value={report.summary?.total_findings || 0} 
                  color="zinc"
                />
                <SummaryCard 
                  label="Critical" 
                  value={report.summary?.by_severity?.critical || 0} 
                  color="red"
                />
                <SummaryCard 
                  label="High" 
                  value={report.summary?.by_severity?.high || 0} 
                  color="orange"
                />
                <SummaryCard 
                  label="Medium" 
                  value={report.summary?.by_severity?.medium || 0} 
                  color="yellow"
                />
                <SummaryCard 
                  label="Low" 
                  value={report.summary?.by_severity?.low || 0} 
                  color="blue"
                />
              </div>
            </CardContent>
          </Card>

          {/* Findings by Severity */}
          {["critical", "high", "medium", "low", "info"].map((severity) => {
            const findings = report.findings?.[severity] || [];
            if (findings.length === 0) return null;
            
            return (
              <div key={severity} className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className={`w-4 h-4 ${
                    severity === "critical" ? "text-red-500" :
                    severity === "high" ? "text-orange-500" :
                    severity === "medium" ? "text-yellow-500" :
                    severity === "low" ? "text-blue-500" : "text-emerald-500"
                  }`} />
                  <h3 className="font-mono text-sm uppercase tracking-wider text-zinc-400">
                    {severity} Severity ({findings.length})
                  </h3>
                </div>
                
                <div className="space-y-3">
                  {findings.map((finding, index) => (
                    <Card key={finding.id || index} className="card-default">
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3 mb-3">
                          <Badge className={`${severityColors[severity]} font-mono text-[10px] uppercase`}>
                            {severity}
                          </Badge>
                          <div className="flex-1">
                            <h4 className="font-mono text-sm text-zinc-100 mb-1">
                              {finding.title}
                            </h4>
                            <p className="font-mono text-xs text-zinc-500">
                              {finding.vulnerability_type}
                            </p>
                          </div>
                        </div>
                        
                        <div className="space-y-3">
                          <div>
                            <h5 className="font-mono text-xs text-zinc-500 uppercase mb-1">
                              Description
                            </h5>
                            <p className="font-mono text-sm text-zinc-300">
                              {finding.description}
                            </p>
                          </div>
                          
                          <div>
                            <h5 className="font-mono text-xs text-zinc-500 uppercase mb-1">
                              Evidence
                            </h5>
                            <div className="code-block text-emerald-400 text-xs">
                              {finding.evidence}
                            </div>
                          </div>
                          
                          {finding.recommendations?.length > 0 && (
                            <div>
                              <h5 className="font-mono text-xs text-zinc-500 uppercase mb-1">
                                Recommendations
                              </h5>
                              <ul className="space-y-1">
                                {finding.recommendations.map((rec, idx) => (
                                  <li key={idx} className="font-mono text-xs text-zinc-300 flex items-start gap-2">
                                    <span className="text-emerald-500">•</span>
                                    {rec}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            );
          })}

          {report.summary?.total_findings === 0 && (
            <Card className="card-default">
              <CardContent className="p-12 text-center">
                <Shield className="w-12 h-12 text-emerald-500/30 mx-auto mb-4" />
                <h3 className="font-mono text-lg text-zinc-200 mb-2">No Findings</h3>
                <p className="font-mono text-sm text-zinc-500">
                  No vulnerabilities have been recorded for this session yet
                </p>
              </CardContent>
            </Card>
          )}
        </ScrollArea>
      ) : (
        <Card className="card-default">
          <CardContent className="p-12 text-center">
            <FileText className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
            <h3 className="font-mono text-lg text-zinc-200 mb-2">Report Unavailable</h3>
            <p className="font-mono text-sm text-zinc-500">
              Unable to generate report for this session
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function SummaryCard({ label, value, color }) {
  const colorClasses = {
    zinc: "text-zinc-100",
    red: "text-red-500",
    orange: "text-orange-500",
    yellow: "text-yellow-500",
    blue: "text-blue-500",
    emerald: "text-emerald-500",
  };

  return (
    <div className="bg-zinc-900/50 border border-zinc-800 p-3 text-center">
      <div className={`font-mono text-2xl font-bold ${colorClasses[color]}`}>
        {value}
      </div>
      <div className="font-mono text-xs text-zinc-500 uppercase tracking-wider mt-1">
        {label}
      </div>
    </div>
  );
}
