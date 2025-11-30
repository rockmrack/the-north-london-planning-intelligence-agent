'use client';

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface StreamingMessageProps {
  content: string;
  isStreaming: boolean;
}

export function StreamingMessage({ content, isStreaming }: StreamingMessageProps) {
  const [displayedContent, setDisplayedContent] = useState('');
  const [cursorVisible, setCursorVisible] = useState(true);

  // Animate cursor blink
  useEffect(() => {
    if (!isStreaming) {
      setCursorVisible(false);
      return;
    }

    const interval = setInterval(() => {
      setCursorVisible((prev) => !prev);
    }, 500);

    return () => clearInterval(interval);
  }, [isStreaming]);

  // Update displayed content as it streams in
  useEffect(() => {
    setDisplayedContent(content);
  }, [content]);

  return (
    <div className="prose prose-sm max-w-none">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {displayedContent}
      </ReactMarkdown>
      {isStreaming && cursorVisible && (
        <span className="inline-block w-2 h-4 bg-primary-600 animate-pulse ml-0.5" />
      )}
    </div>
  );
}
