/* eslint-disable @typescript-eslint/no-explicit-any */

"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Mic, Send, StopCircle, User, Bot, Play } from "lucide-react";
import { useChat } from "@ai-sdk/react";

export default function InterviewsPage() {
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { messages, input, handleInputChange, handleSubmit, isLoading } = (useChat as any)({
    api: '/api/chat',
    body: {
      context: {
        company: 'TechNova',
        role: 'Senior Frontend Engineer',
        type: 'technical'
      }
    },
    initialMessages: [
      {
        id: 'initial-1',
        role: 'assistant',
        content: '¡Hola! Soy tu entrevistador de IA. Hoy simularemos una entrevista para el rol de Senior Frontend Engineer en TechNova. ¿Estás listo para comenzar?'
      }
    ]
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);
    
  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input?.trim()) return;
    handleSubmit(e);
  };

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-heading font-bold text-white tracking-tight">Simulador de Entrevistas</h1>
        <p className="text-zinc-400 mt-1">Practica con IA para tus próximas entrevistas técnicas y de RRHH.</p>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex gap-6 min-h-0">
        
        {/* Chat Window */}
        <Card className="flex-1 flex flex-col bg-zinc-900/40 border-white/10 overflow-hidden">
          <CardContent className="flex-1 p-0 flex flex-col">
            
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {(messages as any[]).map((msg, i) => (
                <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                    msg.role === 'user' ? 'bg-indigo-500 text-white' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  }`}>
                    {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>
                  <div className={`px-4 py-3 rounded-2xl max-w-[80%] ${
                    msg.role === 'user' 
                      ? 'bg-indigo-600 text-white rounded-tr-sm' 
                      : 'bg-zinc-800 text-zinc-200 rounded-tl-sm border border-white/5'
                  }`}>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{(msg as any).content}</p>
                  </div>
                </div>
              ))}
              {isLoading && messages[messages.length - 1]?.role === 'user' && (
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    <Bot className="w-4 h-4 animate-pulse" />
                  </div>
                  <div className="px-4 py-3 rounded-2xl bg-zinc-800 text-zinc-200 rounded-tl-sm border border-white/5 flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-zinc-950/50 border-t border-white/5 backdrop-blur-sm">
              <div className="flex items-end gap-2">
                <button 
                  onClick={() => setIsRecording(!isRecording)}
                  className={`p-3 rounded-xl transition-all flex-shrink-0 ${
                    isRecording 
                      ? 'bg-rose-500/20 text-rose-400 hover:bg-rose-500/30 border border-rose-500/50 animate-pulse' 
                      : 'bg-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-700'
                  }`}
                >
                  {isRecording ? <StopCircle className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                </button>
                <form onSubmit={onSubmit} className="flex-1 flex items-end gap-2 relative">
                  <textarea 
                    value={input}
                    onChange={handleInputChange}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        onSubmit(e);
                      }
                    }}
                    placeholder="Escribe tu respuesta..."
                    className="w-full bg-zinc-900 border border-white/10 rounded-xl py-3 px-4 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all resize-none min-h-[50px] max-h-[150px]"
                    rows={1}
                    disabled={isLoading}
                  />
                  <Button 
                    type="submit"
                    disabled={!input?.trim() || isLoading}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white h-[50px] px-6 rounded-xl shrink-0"
                  >
                    <Send className="w-4 h-4 mr-2" />
                    Enviar
                  </Button>
                </form>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Sidebar Info */}
        <div className="w-80 hidden xl:flex flex-col gap-4">
          <Card className="bg-zinc-900/40 border-white/10 p-5">
            <h3 className="font-semibold text-white mb-4">Contexto de la Entrevista</h3>
            
            <div className="space-y-4">
              <div>
                <div className="text-xs text-zinc-500 mb-1">Empresa</div>
                <div className="text-sm text-zinc-200 font-medium">TechNova</div>
              </div>
              <div>
                <div className="text-xs text-zinc-500 mb-1">Rol</div>
                <div className="text-sm text-zinc-200 font-medium">Senior Frontend Engineer</div>
              </div>
              <div>
                <div className="text-xs text-zinc-500 mb-1">Tipo de Entrevista</div>
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-xs font-medium border border-indigo-500/20">
                  Técnica
                </div>
              </div>
            </div>
          </Card>

          <Card className="bg-zinc-900/40 border-white/10 p-5 flex-1">
            <h3 className="font-semibold text-white mb-4">Feedback en Tiempo Real</h3>
            <div className="flex flex-col items-center justify-center h-40 text-center">
              <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-3">
                <Play className="w-5 h-5 text-zinc-500" />
              </div>
              <p className="text-sm text-zinc-400">El feedback aparecerá aquí mientras hablas.</p>
            </div>
          </Card>
        </div>

      </div>
    </div>
  );
}
