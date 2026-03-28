import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { 
  Shield, 
  AlertTriangle, 
  Activity, 
  Target,
  TrendingUp,
  Clock,
  Zap,
  ChevronRight,
  Flame
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const severityColors = {
  critical: "badge-critical",
  high: "badge-high",
  medium: "badge-medium",
  low: "badge-low",
  info: "badge-info"
};

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="spinner mx-auto mb-4" />
          <p className="font-mono text-sm text-zinc-500">INITIALIZING SYSTEMS...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 stagger-children" data-testid="dashboard-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl font-bold text-zinc-100 tracking-tight">
            COMMAND CENTER
          </h1>
          <p className="font-mono text-sm text-zinc-500 mt-1">
            Real-time security monitoring dashboard
          </p>
        </div>
        <Link to="/sessions">
          <Button className="btn-primary px-6 py-2" data-testid="new-hunt-btn">
            <Flame className="w-4 h-4 mr-2" />
            New Hunt
          </Button>
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          icon={Target}
          label="Active Sessions"
          value={stats?.active_sessions || 0}
          total={stats?.total_sessions || 0}
          color="emerald"
          testId="stat-sessions"
        />
        <StatCard 
          icon={Shield}
          label="Total Findings"
          value={stats?.total_findings || 0}
          color="amber"
          testId="stat-findings"
        />
        <StatCard 
          icon={AlertTriangle}
          label="Critical Issues"
          value={stats?.critical_findings || 0}
          color="red"
          testId="stat-critical"
        />
        <StatCard 
          icon={Activity}
          label="Requests Analyzed"
          value={stats?.requests_analyzed || 0}
          color="blue"
          testId="stat-requests"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Severity Breakdown */}
        <Card className="card-default col-span-1" data-testid="severity-breakdown">
          <CardHeader className="pb-3">
            <CardTitle className="font-mono text-sm uppercase tracking-wider text-zinc-400">
              Severity Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <SeverityBar label="Critical" count={stats?.critical_findings || 0} total={stats?.total_findings || 1} color="red" />
              <SeverityBar label="High" count={stats?.high_findings || 0} total={stats?.total_findings || 1} color="orange" />
              <SeverityBar label="Medium" count={stats?.medium_findings || 0} total={stats?.total_findings || 1} color="yellow" />
              <SeverityBar label="Low" count={stats?.low_findings || 0} total={stats?.total_findings || 1} color="blue" />
              <SeverityBar label="Info" count={stats?.info_findings || 0} total={stats?.total_findings || 1} color="emerald" />
            </div>
          </CardContent>
        </Card>

        {/* Recent Findings */}
        <Card className="card-default col-span-1 lg:col-span-2" data-testid="recent-findings">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <CardTitle className="font-mono text-sm uppercase tracking-wider text-zinc-400">
              Recent Findings
            </CardTitle>
            <Link to="/findings" className="text-emerald-500 hover:text-emerald-400 transition-colors">
              <span className="font-mono text-xs uppercase tracking-wider flex items-center gap-1">
                View All <ChevronRight className="w-3 h-3" />
              </span>
            </Link>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[280px]">
              {stats?.recent_findings?.length > 0 ? (
                <div className="space-y-3">
                  {stats.recent_findings.map((finding, index) => (
                    <div 
                      key={finding.id || index}
                      className="p-3 bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge className={`${severityColors[finding.severity]} font-mono text-[10px] px-2 py-0`}>
                              {finding.severity?.toUpperCase()}
                            </Badge>
                            <span className="font-mono text-xs text-zinc-500">
                              {finding.vulnerability_type}
                            </span>
                          </div>
                          <p className="font-mono text-sm text-zinc-200 truncate">
                            {finding.title}
                          </p>
                        </div>
                        <Clock className="w-3 h-3 text-zinc-600 flex-shrink-0 mt-1" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center py-8">
                  <Shield className="w-12 h-12 text-zinc-700 mb-3" />
                  <p className="font-mono text-sm text-zinc-500">No findings yet</p>
                  <p className="font-mono text-xs text-zinc-600 mt-1">
                    Start a hunting session to discover vulnerabilities
                  </p>
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="card-terminal" data-testid="quick-actions">
        <div className="scanlines" />
        <CardContent className="p-6 relative z-20">
          <div className="flex items-center gap-3 mb-4">
            <Zap className="w-5 h-5 text-emerald-500" />
            <h3 className="font-mono text-sm uppercase tracking-wider text-emerald-500">
              Quick Actions
            </h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Link to="/sessions">
              <Button variant="outline" className="btn-outline w-full justify-start" data-testid="action-new-session">
                <Target className="w-4 h-4 mr-2" />
                New Session
              </Button>
            </Link>
            <Link to="/chat">
              <Button variant="outline" className="btn-outline w-full justify-start" data-testid="action-ai-chat">
                <Activity className="w-4 h-4 mr-2" />
                AI Chat
              </Button>
            </Link>
            <Link to="/findings">
              <Button variant="outline" className="btn-outline w-full justify-start" data-testid="action-view-findings">
                <Shield className="w-4 h-4 mr-2" />
                View Findings
              </Button>
            </Link>
            <Link to="/settings">
              <Button variant="outline" className="btn-outline w-full justify-start" data-testid="action-settings">
                <TrendingUp className="w-4 h-4 mr-2" />
                Configure AI
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, total, color, testId }) {
  const colorClasses = {
    emerald: "text-emerald-500 bg-emerald-500/10 border-emerald-500/30",
    amber: "text-amber-500 bg-amber-500/10 border-amber-500/30",
    red: "text-red-500 bg-red-500/10 border-red-500/30",
    blue: "text-blue-500 bg-blue-500/10 border-blue-500/30",
  };

  return (
    <div className="stat-card" data-testid={testId}>
      <div className="flex items-start justify-between">
        <div>
          <div className="stat-value text-zinc-100">{value}</div>
          {total !== undefined && (
            <div className="font-mono text-xs text-zinc-600 mt-1">
              of {total} total
            </div>
          )}
          <div className="stat-label">{label}</div>
        </div>
        <div className={`p-2 border ${colorClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}

function SeverityBar({ label, count, total, color }) {
  const percentage = total > 0 ? (count / total) * 100 : 0;
  const colorClasses = {
    red: "bg-red-500",
    orange: "bg-orange-500",
    yellow: "bg-yellow-500",
    blue: "bg-blue-500",
    emerald: "bg-emerald-500",
  };

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs text-zinc-400">{label}</span>
        <span className="font-mono text-xs text-zinc-200">{count}</span>
      </div>
      <div className="h-1.5 bg-zinc-800">
        <div 
          className={`h-full ${colorClasses[color]} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
