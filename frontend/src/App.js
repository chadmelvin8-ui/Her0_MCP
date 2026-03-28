import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import Dashboard from "@/pages/Dashboard";
import Sessions from "@/pages/Sessions";
import Chat from "@/pages/Chat";
import Findings from "@/pages/Findings";
import ProxyHistory from "@/pages/ProxyHistory";
import Settings from "@/pages/Settings";
import Reports from "@/pages/Reports";
import Layout from "@/components/Layout";

function App() {
  return (
    <div className="app-container">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="sessions" element={<Sessions />} />
            <Route path="chat/:sessionId?" element={<Chat />} />
            <Route path="findings" element={<Findings />} />
            <Route path="proxy-history/:sessionId?" element={<ProxyHistory />} />
            <Route path="reports/:sessionId?" element={<Reports />} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster 
        position="bottom-right" 
        toastOptions={{
          style: {
            background: '#18181b',
            border: '1px solid #27272a',
            color: '#f4f4f5',
            fontFamily: 'JetBrains Mono, monospace',
          },
        }}
      />
    </div>
  );
}

export default App;
