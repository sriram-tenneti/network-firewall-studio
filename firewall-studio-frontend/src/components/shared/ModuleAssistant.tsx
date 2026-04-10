import { useState, useRef, useEffect, useCallback } from 'react';
import { MessageCircle, X, Send, ChevronDown, ChevronUp, Loader2, Sparkles, BookOpen, BarChart3, AlertTriangle, Settings, ArrowRight, Plus, Code, Shield, List, FileText, Clock, CheckCircle, Lightbulb, GitMerge, Layers, MapPin, Server, Grid3X3, Tag, Info, Activity, GitBranch, Download, UserPlus, Map, Copy, History, PieChart, Edit } from 'lucide-react';
import { queryAssistant, getModuleServices } from '@/lib/api';
import type { AssistantService, AssistantResponse } from '@/lib/api';

// Icon mapping for service catalog
const ICON_MAP: Record<string, React.ReactNode> = {
  'plus': <Plus className="w-3.5 h-3.5" />,
  'edit': <Edit className="w-3.5 h-3.5" />,
  'code': <Code className="w-3.5 h-3.5" />,
  'send': <ArrowRight className="w-3.5 h-3.5" />,
  'layers': <Layers className="w-3.5 h-3.5" />,
  'shield': <Shield className="w-3.5 h-3.5" />,
  'list': <List className="w-3.5 h-3.5" />,
  'bar-chart': <BarChart3 className="w-3.5 h-3.5" />,
  'alert-triangle': <AlertTriangle className="w-3.5 h-3.5" />,
  'book': <BookOpen className="w-3.5 h-3.5" />,
  'arrow-right': <ArrowRight className="w-3.5 h-3.5" />,
  'pie-chart': <PieChart className="w-3.5 h-3.5" />,
  'lightbulb': <Lightbulb className="w-3.5 h-3.5" />,
  'check-circle': <CheckCircle className="w-3.5 h-3.5" />,
  'git-merge': <GitMerge className="w-3.5 h-3.5" />,
  'file-text': <FileText className="w-3.5 h-3.5" />,
  'user-plus': <UserPlus className="w-3.5 h-3.5" />,
  'grid': <Grid3X3 className="w-3.5 h-3.5" />,
  'map': <Map className="w-3.5 h-3.5" />,
  'map-pin': <MapPin className="w-3.5 h-3.5" />,
  'server': <Server className="w-3.5 h-3.5" />,
  'tag': <Tag className="w-3.5 h-3.5" />,
  'info': <Info className="w-3.5 h-3.5" />,
  'clock': <Clock className="w-3.5 h-3.5" />,
  'check': <CheckCircle className="w-3.5 h-3.5" />,
  'x': <X className="w-3.5 h-3.5" />,
  'history': <History className="w-3.5 h-3.5" />,
  'activity': <Activity className="w-3.5 h-3.5" />,
  'git-branch': <GitBranch className="w-3.5 h-3.5" />,
  'download': <Download className="w-3.5 h-3.5" />,
  'copy': <Copy className="w-3.5 h-3.5" />,
  'settings': <Settings className="w-3.5 h-3.5" />,
};

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  intent?: string;
  suggestions?: string[];
  data?: Record<string, unknown> | null;
  actions_taken?: string[];
  error?: string | null;
  services?: AssistantService[];
}

interface ModuleAssistantProps {
  module: string;
  context?: Record<string, unknown>;
  userRole?: string;
}

export function ModuleAssistant({ module, context, userRole = 'admin' }: ModuleAssistantProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [services, setServices] = useState<AssistantService[]>([]);
  const [showCatalog, setShowCatalog] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load module services on mount
  useEffect(() => {
    if (isOpen && services.length === 0) {
      getModuleServices(module, userRole)
        .then(res => setServices(res.services))
        .catch(() => { /* silent */ });
    }
  }, [isOpen, module, userRole, services.length]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && !isMinimized) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen, isMinimized]);

  // Add welcome message on first open
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      const moduleNames: Record<string, string> = {
        'design-studio': 'Design Studio',
        'migration': 'Migration Studio',
        'firewall-management': 'Firewall Management',
        'data-import': 'Data Import',
        'settings': 'Settings',
        'review': 'Review & Approval',
        'lifecycle': 'Lifecycle Dashboard',
      };
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: `Welcome to the **${moduleNames[module] || module}** Assistant! I can help you with tasks, answer questions, generate reports, and diagnose issues. Type a question or click a suggestion below.`,
        timestamp: new Date(),
        suggestions: ['What can you do?', 'Show me metrics', 'Help with an error'],
      }]);
    }
  }, [isOpen, messages.length, module]);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response: AssistantResponse = await queryAssistant(module, text.trim(), context, userRole);
      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        intent: response.intent,
        suggestions: response.suggestions,
        data: response.data,
        actions_taken: response.actions_taken,
        error: response.error,
        services: response.services,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please make sure the backend is running and try again.',
        timestamp: new Date(),
        error: err instanceof Error ? err.message : 'Unknown error',
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, module, context, userRole]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  // Format markdown-like text to JSX
  const formatMessage = (text: string) => {
    const lines = text.split('\n');
    return lines.map((line, i) => {
      // Bold
      let formatted = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      // Code
      formatted = formatted.replace(/`(.+?)`/g, '<code class="px-1 py-0.5 bg-slate-100 rounded text-xs font-mono">$1</code>');
      // Bullet points
      if (formatted.startsWith('• ') || formatted.startsWith('- ')) {
        return <div key={i} className="ml-3 flex gap-1.5 mt-0.5"><span className="text-blue-400 shrink-0">&#x2022;</span><span dangerouslySetInnerHTML={{ __html: formatted.slice(2) }} /></div>;
      }
      // Numbered list
      const numMatch = formatted.match(/^(\d+)\.\s/);
      if (numMatch) {
        return <div key={i} className="ml-3 flex gap-1.5 mt-0.5"><span className="text-blue-400 font-semibold shrink-0">{numMatch[1]}.</span><span dangerouslySetInnerHTML={{ __html: formatted.slice(numMatch[0].length) }} /></div>;
      }
      // Empty line
      if (!formatted.trim()) return <div key={i} className="h-1.5" />;
      return <div key={i} dangerouslySetInnerHTML={{ __html: formatted }} />;
    });
  };

  // Floating button when closed
  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-full p-3.5 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200 group"
        title="Open Module Assistant"
      >
        <MessageCircle className="w-6 h-6" />
        <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-white animate-pulse" />
        <span className="absolute bottom-full right-0 mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
          AI Assistant
        </span>
      </button>
    );
  }

  // Minimized state
  if (isMinimized) {
    return (
      <div className="fixed bottom-6 right-6 z-50 bg-white rounded-xl shadow-xl border border-slate-200 w-72 cursor-pointer" onClick={() => setIsMinimized(false)}>
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-900">AI Assistant</div>
              <div className="text-[10px] text-slate-500">{messages.length} messages</div>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button onClick={(e) => { e.stopPropagation(); setIsMinimized(false); }} className="p-1 hover:bg-slate-100 rounded">
              <ChevronUp className="w-4 h-4 text-slate-400" />
            </button>
            <button onClick={(e) => { e.stopPropagation(); setIsOpen(false); setIsMinimized(false); }} className="p-1 hover:bg-slate-100 rounded">
              <X className="w-4 h-4 text-slate-400" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Full chat panel
  return (
    <div className="fixed bottom-6 right-6 z-50 w-[420px] h-[600px] bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden animate-in slide-in-from-bottom-4 duration-300">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">Module Assistant</div>
            <div className="text-[10px] text-white/70 capitalize">{module.replace(/-/g, ' ')}</div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowCatalog(!showCatalog)}
            className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
            title="Service Catalog"
          >
            <BookOpen className="w-4 h-4 text-white/80" />
          </button>
          <button
            onClick={() => setIsMinimized(true)}
            className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
            title="Minimize"
          >
            <ChevronDown className="w-4 h-4 text-white/80" />
          </button>
          <button
            onClick={() => { setIsOpen(false); setIsMinimized(false); }}
            className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
            title="Close"
          >
            <X className="w-4 h-4 text-white/80" />
          </button>
        </div>
      </div>

      {/* Service Catalog Drawer */}
      {showCatalog && (
        <div className="border-b border-slate-200 bg-slate-50 px-3 py-2 max-h-[200px] overflow-y-auto shrink-0">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Service Catalog</div>
          <div className="grid grid-cols-2 gap-1">
            {services.map(svc => (
              <button
                key={svc.id}
                onClick={() => { handleSuggestionClick(svc.name); setShowCatalog(false); }}
                className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg hover:bg-white border border-transparent hover:border-slate-200 text-left transition-colors group"
              >
                <span className="text-blue-500 group-hover:text-blue-600">
                  {ICON_MAP[svc.icon] || <Sparkles className="w-3.5 h-3.5" />}
                </span>
                <div>
                  <div className="text-[11px] font-medium text-slate-700 leading-tight">{svc.name}</div>
                  <div className="text-[9px] text-slate-400 leading-tight line-clamp-1">{svc.description}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[90%] ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-2xl rounded-br-md px-3.5 py-2' : ''}`}>
              {msg.role === 'assistant' && (
                <div className="flex items-start gap-2">
                  <div className="w-6 h-6 rounded-lg bg-gradient-to-r from-blue-100 to-indigo-100 flex items-center justify-center shrink-0 mt-0.5">
                    <Sparkles className="w-3 h-3 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-[12px] text-slate-800 leading-relaxed">
                      {formatMessage(msg.content)}
                    </div>

                    {/* Error indicator */}
                    {msg.error && (
                      <div className="mt-2 flex items-center gap-1.5 text-[10px] text-amber-600 bg-amber-50 rounded-lg px-2 py-1">
                        <AlertTriangle className="w-3 h-3 shrink-0" />
                        <span>{msg.error}</span>
                      </div>
                    )}

                    {/* Actions taken */}
                    {msg.actions_taken && msg.actions_taken.length > 0 && (
                      <div className="mt-2 space-y-0.5">
                        {msg.actions_taken.map((action, i) => (
                          <div key={i} className="flex items-center gap-1.5 text-[10px] text-green-700 bg-green-50 rounded-lg px-2 py-1">
                            <CheckCircle className="w-3 h-3 shrink-0" />
                            <span>{action}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Data preview (metrics tables) */}
                    {msg.data && Object.keys(msg.data).length > 0 && msg.intent && ['metrics', 'count_rules', 'count_groups', 'count_apps', 'rule_metrics'].includes(msg.intent) && (
                      <div className="mt-2 bg-slate-50 rounded-lg border border-slate-200 p-2 overflow-x-auto">
                        <div className="text-[9px] font-bold text-slate-500 uppercase tracking-wider mb-1">Data Summary</div>
                        <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[10px]">
                          {Object.entries(msg.data).filter(([k]) => typeof msg.data![k] === 'number' || typeof msg.data![k] === 'string').slice(0, 12).map(([k, v]) => (
                            <div key={k} className="flex justify-between gap-2">
                              <span className="text-slate-500 truncate">{k.replace(/_/g, ' ')}</span>
                              <span className="text-slate-800 font-semibold">{String(v)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Service cards (shown on catalog request) */}
                    {msg.services && msg.services.length > 0 && (
                      <div className="mt-2 grid grid-cols-2 gap-1">
                        {msg.services.slice(0, 6).map(svc => (
                          <button
                            key={svc.id}
                            onClick={() => handleSuggestionClick(svc.name)}
                            className="flex items-center gap-1.5 px-2 py-1.5 bg-white rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50 text-left transition-colors"
                          >
                            <span className="text-blue-500">{ICON_MAP[svc.icon] || <Sparkles className="w-3.5 h-3.5" />}</span>
                            <span className="text-[10px] font-medium text-slate-700 truncate">{svc.name}</span>
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Suggestion chips */}
                    {msg.suggestions && msg.suggestions.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {msg.suggestions.slice(0, 4).map((s, i) => (
                          <button
                            key={i}
                            onClick={() => handleSuggestionClick(s)}
                            className="text-[10px] px-2 py-1 rounded-full bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition-colors whitespace-nowrap"
                          >
                            {s}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {msg.role === 'user' && (
                <div className="text-[12px] leading-relaxed">{msg.content}</div>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-lg bg-gradient-to-r from-blue-100 to-indigo-100 flex items-center justify-center">
                <Loader2 className="w-3 h-3 text-blue-600 animate-spin" />
              </div>
              <div className="flex gap-1 px-3 py-2">
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-slate-200 px-3 py-2.5 bg-white shrink-0">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything..."
            className="flex-1 text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 placeholder:text-slate-400"
            disabled={isLoading}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isLoading}
            className="p-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <div className="flex items-center justify-between mt-1.5">
          <span className="text-[9px] text-slate-400">
            Role: <span className="font-medium capitalize">{userRole}</span>
          </span>
          <span className="text-[9px] text-slate-400">
            Press Enter to send
          </span>
        </div>
      </div>
    </div>
  );
}
