'use client';

import { useState } from 'react';
import { MessageCircle, X, Minimize2 } from 'lucide-react';
import { ChatWindow } from './ChatWindow';
import { cn } from '@/lib/utils';

export function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);

  return (
    <>
      {/* Chat Button */}
      {!isOpen && (
        <div className="fixed bottom-6 right-6 z-[9999] flex items-center gap-3">
          <div className="bg-white text-gray-800 px-4 py-2 rounded-full shadow-lg font-medium text-sm animate-bounce">
            Planning Permission Assistant
          </div>
          <button
            onClick={() => setIsOpen(true)}
            className={cn(
              'w-14 h-14 rounded-full',
              'bg-blue-700 text-white shadow-lg',
              'flex items-center justify-center',
              'hover:bg-blue-800 transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-blue-500',
              'cursor-pointer'
            )}
            aria-label="Open chat"
            type="button"
          >
            <MessageCircle className="w-6 h-6" />
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white animate-pulse" />
          </button>
        </div>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          className={cn(
            'fixed bottom-6 right-6 z-[9999]',
            'w-[400px] max-w-[calc(100vw-48px)]',
            'bg-white rounded-2xl shadow-2xl',
            'border border-gray-200',
            'overflow-hidden',
            isMinimized ? 'h-auto' : 'h-[600px] max-h-[calc(100vh-48px)]'
          )}
        >
          {/* Header */}
          <div className="bg-blue-700 text-white px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <div>
                <h3 className="font-semibold text-sm">Planning Assistant</h3>
                <p className="text-xs text-blue-200">Hampstead Renovations</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="p-1 hover:bg-blue-600 rounded transition-colors"
                aria-label={isMinimized ? 'Expand' : 'Minimize'}
                type="button"
              >
                <Minimize2 className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 hover:bg-blue-600 rounded transition-colors"
                aria-label="Close"
                type="button"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Chat Content */}
          {!isMinimized && <ChatWindow />}
        </div>
      )}
    </>
  );
}
