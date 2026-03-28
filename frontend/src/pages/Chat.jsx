import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { 
  Send, 
  Trash2, 
  Terminal,
  User,
  Bot,
  Flame,
  AlertCircle,
  ChevronDown,
  Loader2
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const QUICK_COMMANDS = [
  { label: "Find vulnerabilities", command: "Analyze the proxy history for security vulnerabilities. Look for IDOR, XSS, SQLi, and authentication issues." },
  { label: "IDOR Hunt", command: "Focus on finding Insecure Direct Object References. Look for numeric IDs, UUIDs, and parameters that reference user resources." },
  { label: "Auth Analysis", command: "Analyze authentication flows. Check for session management issues, weak tokens, and privilege escalation." },
  { label: "Data Leakage", command: "Search for sensitive data exposure in responses. Look for PII, credentials, internal IPs, and stack traces." },
  { label: "Logic Flaws", command: "Identify business logic vulnerabilities. Look for race conditions, workflow bypass, and state manipulation." },
];

export default function Chat() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(sessionId || "");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    if (selectedSession) {
      fetchMessages();
      navigate(`/chat/${selectedSession}`, { replace: true });
    }
  }, [selectedSession]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

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

  const fetchMessages = async () => {
    if (!selectedSession) return;
    try {
      const response = await axios.get(`${API}/chat/${selectedSession}`);
      setMessages(response.data);
    } catch (error) {
      console.error("Failed to fetch messages:", error);
    }
  };

  const sendMessage = async (content = input) => {
    if (!content.trim() || !selectedSession) return;
    
    setSending(true);
    setInput("");
    
    // Optimistically add user message
    const tempUserMsg = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: content,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);
    
    try {
      const response = await axios.post(`${API}/chat`, {
        session_id: selectedSession,
        content: content
      });
      
      // Replace temp message and add assistant response
      setMessages(prev => [
        ...prev.filter(m => m.id !== tempUserMsg.id),
        response.data.user_message,
        response.data.assistant_message
      ]);
    } catch (error) {
      toast.error("Failed to send message");
      setMessages(prev => prev.filter(m => m.id !== tempUserMsg.id));
      setInput(content);
    } finally {
      setSending(false);
    }
  };

  const clearChat = async () => {
    if (!selectedSession) return;
    try {
      await axios.delete(`${API}/chat/${selectedSession}`);
      setMessages([]);
      toast.success("Chat cleared");
    } catch (error) {
      toast.error("Failed to clear chat");
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
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
      <div className="flex items-center justify-center h-full" data-testid="chat-no-sessions">
        <Card className="card-terminal max-w-md">
          <div className="scanlines" />
          <CardContent className="p-8 text-center relative z-20">
            <Terminal className="w-12 h-12 text-emerald-500/50 mx-auto mb-4" />
            <h3 className="font-mono text-lg text-zinc-200 mb-2">No Sessions Available</h3>
            <p className="font-mono text-sm text-zinc-500 mb-4">
              Create a session first to start chatting with the AI
            </p>
            <Button className="btn-primary" onClick={() => navigate("/sessions")}>
              Create Session
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]" data-testid="chat-page">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Flame className="w-5 h-5 text-emerald-500" />
            <h1 className="font-mono text-lg font-bold text-zinc-100">AI HUNTER</h1>
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
                  className="font-mono text-sm text-zinc-300 focus:bg-zinc-800 focus:text-zinc-100"
                >
                  {session.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button 
          variant="outline" 
          className="btn-outline" 
          onClick={clearChat}
          data-testid="clear-chat-btn"
        >
          <Trash2 className="w-4 h-4 mr-2" />
          Clear
        </Button>
      </div>

      {/* Quick Commands */}
      <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-2">
        {QUICK_COMMANDS.map((cmd, index) => (
          <Button
            key={index}
            size="sm"
            variant="outline"
            className="btn-outline whitespace-nowrap text-xs"
            onClick={() => sendMessage(cmd.command)}
            disabled={sending}
            data-testid={`quick-cmd-${index}`}
          >
            {cmd.label}
          </Button>
        ))}
      </div>

      {/* Chat Area */}
      <Card className="card-terminal flex-1 flex flex-col overflow-hidden">
        <div className="scanlines" />
        <ScrollArea className="flex-1 p-4 relative z-20">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-12">
              <Bot className="w-16 h-16 text-emerald-500/30 mb-4" />
              <h3 className="font-mono text-lg text-zinc-300 mb-2">
                MCP'Arsonist AI Ready
              </h3>
              <p className="font-mono text-sm text-zinc-500 max-w-md">
                I'm your autonomous penetration testing assistant. Ask me to analyze traffic, 
                find vulnerabilities, or use the quick commands above.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, index) => (
                <ChatMessage key={msg.id || index} message={msg} />
              ))}
              {sending && (
                <div className="flex items-center gap-2 text-emerald-500 font-mono text-sm">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Analyzing...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </ScrollArea>

        {/* Input Area */}
        <div className="p-4 border-t border-emerald-500/20 relative z-20">
          <div className="flex items-center gap-2">
            <div className="flex-1 relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 font-mono text-emerald-500 text-sm">
                {">"}
              </span>
              <Input
                className="input-terminal pl-7 pr-4"
                placeholder="Enter command or question..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={sending}
                data-testid="chat-input"
              />
            </div>
            <Button 
              className="btn-primary px-6"
              onClick={() => sendMessage()}
              disabled={sending || !input.trim()}
              data-testid="send-btn"
            >
              {sending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

function ChatMessage({ message }) {
  const isUser = message.role === "user";
  
  return (
    <div className={`chat-message ${isUser ? "user" : "assistant"}`} data-testid={`message-${message.role}`}>
      <div className="flex items-start gap-3">
        <div className={`p-1.5 ${isUser ? "bg-zinc-700" : "bg-emerald-500/20"}`}>
          {isUser ? (
            <User className="w-4 h-4 text-zinc-300" />
          ) : (
            <Bot className="w-4 h-4 text-emerald-500" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-mono text-xs text-zinc-500 mb-1">
            {isUser ? "YOU" : "MCP'ARSONIST AI"}
          </div>
          <div className="font-mono text-sm text-zinc-200 whitespace-pre-wrap break-words">
            {message.content}
          </div>
        </div>
      </div>
    </div>
  );
}
