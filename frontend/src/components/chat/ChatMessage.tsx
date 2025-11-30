'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChevronDown, ChevronUp, FileText, ThumbsUp, ThumbsDown } from 'lucide-react';
import type { Message } from '@/lib/store';
import type { Citation } from '@/lib/api';
import { cn, formatDate, truncateText } from '@/lib/utils';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const [showCitations, setShowCitations] = useState(false);
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null);

  const isUser = message.role === 'user';
  const hasCitations = message.citations && message.citations.length > 0;

  const handleFeedback = async (type: 'positive' | 'negative') => {
    setFeedback(type);
    // TODO: Send feedback to API
  };

  return (
    <div
      className={cn(
        'flex gap-3 animate-fade-in',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          isUser ? 'bg-primary-700' : 'bg-primary-100'
        )}
      >
        <span className="text-sm">{isUser ? '👤' : '🏛️'}</span>
      </div>

      {/* Message Content */}
      <div className={cn('flex flex-col gap-2', isUser ? 'items-end' : 'items-start')}>
        <div
          className={cn(
            'chat-bubble',
            isUser ? 'chat-bubble-user' : 'chat-bubble-assistant'
          )}
        >
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <div className="markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Citations */}
        {!isUser && hasCitations && (
          <div className="w-full max-w-[85%]">
            <button
              onClick={() => setShowCitations(!showCitations)}
              className="flex items-center gap-1 text-xs text-neutral-500 hover:text-neutral-700 transition-colors"
            >
              <FileText className="w-3 h-3" />
              <span>{message.citations!.length} sources</span>
              {showCitations ? (
                <ChevronUp className="w-3 h-3" />
              ) : (
                <ChevronDown className="w-3 h-3" />
              )}
            </button>

            {showCitations && (
              <div className="mt-2 space-y-2">
                {message.citations!.map((citation, index) => (
                  <CitationCard key={index} citation={citation} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Feedback buttons for assistant messages */}
        {!isUser && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-neutral-400">
              {formatDate(new Date(message.timestamp))}
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => handleFeedback('positive')}
                className={cn(
                  'p-1 rounded hover:bg-neutral-100 transition-colors',
                  feedback === 'positive' && 'text-green-600 bg-green-50'
                )}
                aria-label="Helpful"
              >
                <ThumbsUp className="w-3 h-3" />
              </button>
              <button
                onClick={() => handleFeedback('negative')}
                className={cn(
                  'p-1 rounded hover:bg-neutral-100 transition-colors',
                  feedback === 'negative' && 'text-red-600 bg-red-50'
                )}
                aria-label="Not helpful"
              >
                <ThumbsDown className="w-3 h-3" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function CitationCard({ citation }: { citation: Citation }) {
  return (
    <div className="citation-card">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-neutral-900 truncate">
            {citation.document_name}
          </p>
          <p className="text-xs text-neutral-500">
            {citation.borough}
            {citation.section && ` • ${citation.section}`}
            {citation.page_number && ` • Page ${citation.page_number}`}
          </p>
        </div>
        <div className="flex-shrink-0">
          <span
            className={cn(
              'text-xs px-2 py-0.5 rounded-full',
              citation.relevance_score > 0.9
                ? 'bg-green-100 text-green-700'
                : citation.relevance_score > 0.8
                ? 'bg-yellow-100 text-yellow-700'
                : 'bg-neutral-100 text-neutral-600'
            )}
          >
            {Math.round(citation.relevance_score * 100)}%
          </span>
        </div>
      </div>
      {citation.paragraph && (
        <p className="text-xs text-neutral-600 mt-2 italic">
          "{truncateText(citation.paragraph, 150)}"
        </p>
      )}
    </div>
  );
}
