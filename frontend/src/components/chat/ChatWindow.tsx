'use client';

import { useEffect, useRef, useState } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { ChatMessage } from './ChatMessage';
import { SuggestedQuestions } from './SuggestedQuestions';
import { LeadCaptureForm } from './LeadCaptureForm';
import { useChatStore } from '@/lib/store';
import { sendChatMessage } from '@/lib/api';
import { generateSessionId, cn } from '@/lib/utils';

export function ChatWindow() {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    messages,
    addMessage,
    sessionId,
    setSessionId,
    isLoading,
    setIsLoading,
    suggestedQuestions,
    setSuggestedQuestions,
    requiresEmail,
    setRequiresEmail,
    selectedBorough,
    setDetectedBorough,
    setDetectedLocation,
    incrementQueryCount,
  } = useChatStore();

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Chat mutation
  const chatMutation = useMutation({
    mutationFn: sendChatMessage,
    onMutate: () => {
      setIsLoading(true);
    },
    onSuccess: (response) => {
      // Update session ID
      if (!sessionId) {
        setSessionId(response.session_id);
      }

      // Add assistant message
      addMessage({
        role: 'assistant',
        content: response.message,
        citations: response.citations,
      });

      // Update state
      setSuggestedQuestions(response.suggested_questions);
      setDetectedBorough(response.detected_borough);
      setDetectedLocation(response.detected_location);
      incrementQueryCount();

      if (response.requires_email) {
        setRequiresEmail(true);
      }
    },
    onError: (error) => {
      addMessage({
        role: 'assistant',
        content:
          "I apologize, but I'm having trouble processing your request. Please try again in a moment.",
      });
    },
    onSettled: () => {
      setIsLoading(false);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const message = input.trim();
    if (!message || isLoading) return;

    // Add user message
    addMessage({
      role: 'user',
      content: message,
    });

    // Clear input
    setInput('');

    // Send to API
    const currentSessionId = sessionId || generateSessionId();
    if (!sessionId) {
      setSessionId(currentSessionId);
    }

    chatMutation.mutate({
      message,
      session_id: currentSessionId,
      borough: selectedBorough || undefined,
    });
  };

  const handleSuggestionClick = (question: string) => {
    setInput(question);
    inputRef.current?.focus();
  };

  // Show lead capture form if required
  if (requiresEmail) {
    return <LeadCaptureForm />;
  }

  return (
    <div className="flex flex-col h-[calc(600px-52px)]">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">🏠</div>
            <h4 className="font-semibold text-neutral-900 mb-2">
              Planning Permission Assistant
            </h4>
            <p className="text-sm text-neutral-600 mb-4">
              Ask me about planning permission requirements for your renovation
              project in North London.
            </p>
            <SuggestedQuestions
              questions={[
                { question: 'Can I extend my house in Hampstead?' },
                { question: 'What are the rules for loft conversions?' },
                { question: 'Do I need permission for a basement?' },
              ]}
              onSelect={handleSuggestionClick}
            />
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                  <span className="text-sm">🏛️</span>
                </div>
                <div className="chat-bubble chat-bubble-assistant">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            {!isLoading && suggestedQuestions.length > 0 && (
              <SuggestedQuestions
                questions={suggestedQuestions}
                onSelect={handleSuggestionClick}
              />
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-neutral-200 p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about planning permission..."
            disabled={isLoading}
            className={cn(
              'input-field flex-1',
              isLoading && 'opacity-50 cursor-not-allowed'
            )}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className={cn(
              'btn-primary px-3',
              (!input.trim() || isLoading) && 'opacity-50 cursor-not-allowed'
            )}
            aria-label="Send message"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>
        <p className="text-xs text-neutral-500 mt-2 text-center">
          AI-powered guidance based on official planning documents
        </p>
      </div>
    </div>
  );
}
