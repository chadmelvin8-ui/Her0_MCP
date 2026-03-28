import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { 
  Settings as SettingsIcon, 
  Save,
  RefreshCw,
  Server,
  Brain,
  Shield,
  CheckCircle,
  AlertCircle
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AI_PROVIDERS = [
  { value: "openai", label: "OpenAI", models: ["gpt-5.2", "gpt-5.1", "gpt-4o", "o4-mini"] },
  { value: "anthropic", label: "Anthropic", models: ["claude-sonnet-4-5-20250929", "claude-4-sonnet-20250514", "claude-haiku-4-5-20251001"] },
  { value: "gemini", label: "Google Gemini", models: ["gemini-3-flash-preview", "gemini-2.5-pro", "gemini-2.5-flash"] },
  { value: "ollama", label: "Ollama (Local)", models: ["llama3.2", "mistral", "codellama", "mixtral"] },
];

export default function Settings() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await axios.get(`${API}/config`);
      setConfig(response.data);
    } catch (error) {
      toast.error("Failed to fetch configuration");
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      const response = await axios.put(`${API}/config`, {
        ai_provider: config.ai_provider,
        ai_model: config.ai_model,
        burp_host: config.burp_host,
        burp_port: config.burp_port,
        ollama_url: config.ollama_url,
      });
      setConfig(response.data);
      toast.success("Configuration saved");
    } catch (error) {
      toast.error("Failed to save configuration");
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async () => {
    setConnectionStatus("testing");
    try {
      const response = await axios.get(`${API}/health`);
      if (response.data.status === "healthy") {
        setConnectionStatus("connected");
        toast.success("Connection successful");
      }
    } catch (error) {
      setConnectionStatus("error");
      toast.error("Connection failed");
    }
  };

  const getModelsForProvider = () => {
    const provider = AI_PROVIDERS.find(p => p.value === config?.ai_provider);
    return provider?.models || [];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-3xl" data-testid="settings-page">
      {/* Header */}
      <div>
        <h1 className="font-mono text-2xl font-bold text-zinc-100 tracking-tight">
          CONFIGURATION
        </h1>
        <p className="font-mono text-sm text-zinc-500 mt-1">
          Configure AI providers and Burp Suite connection
        </p>
      </div>

      {/* AI Provider Settings */}
      <Card className="card-default">
        <CardHeader className="pb-4">
          <CardTitle className="font-mono text-sm uppercase tracking-wider text-zinc-400 flex items-center gap-2">
            <Brain className="w-4 h-4" />
            AI Provider
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="font-mono text-xs text-zinc-400 uppercase tracking-wider">
                Provider
              </Label>
              <Select 
                value={config?.ai_provider || "openai"} 
                onValueChange={(v) => {
                  const provider = AI_PROVIDERS.find(p => p.value === v);
                  setConfig({ 
                    ...config, 
                    ai_provider: v,
                    ai_model: provider?.models[0] || ""
                  });
                }}
              >
                <SelectTrigger className="input-terminal" data-testid="provider-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800">
                  {AI_PROVIDERS.map((provider) => (
                    <SelectItem 
                      key={provider.value} 
                      value={provider.value}
                      className="font-mono text-sm"
                    >
                      {provider.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label className="font-mono text-xs text-zinc-400 uppercase tracking-wider">
                Model
              </Label>
              <Select 
                value={config?.ai_model || ""} 
                onValueChange={(v) => setConfig({ ...config, ai_model: v })}
              >
                <SelectTrigger className="input-terminal" data-testid="model-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800">
                  {getModelsForProvider().map((model) => (
                    <SelectItem 
                      key={model} 
                      value={model}
                      className="font-mono text-sm"
                    >
                      {model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {config?.ai_provider === "ollama" && (
            <div className="space-y-2">
              <Label className="font-mono text-xs text-zinc-400 uppercase tracking-wider">
                Ollama URL
              </Label>
              <Input
                className="input-terminal"
                value={config?.ollama_url || "http://localhost:11434"}
                onChange={(e) => setConfig({ ...config, ollama_url: e.target.value })}
                placeholder="http://localhost:11434"
                data-testid="ollama-url-input"
              />
            </div>
          )}

          <div className="bg-zinc-800/50 border border-zinc-700 p-3 mt-4">
            <p className="font-mono text-xs text-zinc-400">
              <span className="text-emerald-500">Note:</span> For OpenAI, Anthropic, and Gemini, the Emergent Universal Key is used automatically. 
              For Ollama, ensure the local server is running.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Burp Suite Settings */}
      <Card className="card-default">
        <CardHeader className="pb-4">
          <CardTitle className="font-mono text-sm uppercase tracking-wider text-zinc-400 flex items-center gap-2">
            <Server className="w-4 h-4" />
            Burp Suite MCP Server
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="font-mono text-xs text-zinc-400 uppercase tracking-wider">
                Host
              </Label>
              <Input
                className="input-terminal"
                value={config?.burp_host || "127.0.0.1"}
                onChange={(e) => setConfig({ ...config, burp_host: e.target.value })}
                placeholder="127.0.0.1"
                data-testid="burp-host-input"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="font-mono text-xs text-zinc-400 uppercase tracking-wider">
                Port
              </Label>
              <Input
                className="input-terminal"
                type="number"
                value={config?.burp_port || 9876}
                onChange={(e) => setConfig({ ...config, burp_port: parseInt(e.target.value) })}
                placeholder="9876"
                data-testid="burp-port-input"
              />
            </div>
          </div>

          <div className="bg-zinc-800/50 border border-zinc-700 p-3">
            <p className="font-mono text-xs text-zinc-400">
              <span className="text-amber-500">Setup Required:</span> Install the MCP Server extension in Burp Suite 
              from <a href="https://github.com/PortSwigger/mcp-server" target="_blank" rel="noopener noreferrer" className="text-emerald-500 hover:underline">PortSwigger/mcp-server</a>
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Connection Status */}
      <Card className="card-terminal">
        <div className="scanlines" />
        <CardContent className="p-4 relative z-20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="w-5 h-5 text-emerald-500" />
              <div>
                <p className="font-mono text-sm text-zinc-200">System Status</p>
                <p className="font-mono text-xs text-zinc-500">
                  {connectionStatus === "connected" && "All systems operational"}
                  {connectionStatus === "error" && "Connection issues detected"}
                  {connectionStatus === "testing" && "Testing connection..."}
                  {!connectionStatus && "Click to test connection"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {connectionStatus === "connected" && (
                <CheckCircle className="w-5 h-5 text-emerald-500" />
              )}
              {connectionStatus === "error" && (
                <AlertCircle className="w-5 h-5 text-red-500" />
              )}
              <Button 
                variant="outline" 
                className="btn-outline"
                onClick={testConnection}
                disabled={connectionStatus === "testing"}
                data-testid="test-connection-btn"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${connectionStatus === "testing" ? "animate-spin" : ""}`} />
                Test
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button 
          className="btn-primary px-8"
          onClick={saveConfig}
          disabled={saving}
          data-testid="save-config-btn"
        >
          {saving ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          Save Configuration
        </Button>
      </div>
    </div>
  );
}
