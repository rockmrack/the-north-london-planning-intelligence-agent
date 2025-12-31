'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Minimize2 } from 'lucide-react';
import { ChatWindow } from './ChatWindow';
import { useChatStore } from '@/lib/store';
import { cn } from '@/lib/utils';

export function ChatWidget() {
  const { isOpen, setIsOpen } = useChatStore();
  const [isMinimized, setIsMinimized] = useState(false);

  return (
    <>
      {/* Chat Button with Tooltip */}
      <AnimatePresence>
        {!isOpen && (
          <>
            {/* Tooltip */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ delay: 1 }}
              className="fixed bottom-6 right-24 z-50 max-w-xs hidden sm:block"
            >
              <div className="bg-white rounded-lg shadow-lg px-4 py-3 border border-neutral-200">
                <p className="text-sm font-medium text-neutral-900">
                  💡 Thinking of extending?
                </p>
                <p className="text-xs text-neutral-600 mt-1">
                  Ask our AI Planner about local planning rules
                </p>
              </div>
              <div className="absolute -right-2 top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-r border-t border-neutral-200 rotate-45" />
            </motion.div>

            {/* Chat Button */}
            <motion.button
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              onClick={() => setIsOpen(true)}
              className={cn(
                'fixed bottom-6 right-6 z-50',
                'w-14 h-14 rounded-full',
                'bg-primary-700 text-white shadow-lg',
                'flex items-center justify-center',
                'hover:bg-primary-800 transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-primary-700/50',
                'relative'
              )}
              aria-label="Open planning assistant - Thinking of extending? Ask our AI Planner"
            >
              <MessageCircle className="w-6 h-6" />
              {/* Pulse indicator */}
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white animate-pulse" />
            </motion.button>
          </>
        )}
      </AnimatePresence>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{
              opacity: 1,
              y: 0,
              scale: 1,
              height: isMinimized ? 'auto' : undefined,
            }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className={cn(
              'fixed bottom-6 right-6 z-50',
              'w-[400px] max-w-[calc(100vw-48px)]',
              'bg-white rounded-2xl shadow-2xl',
              'border border-neutral-200',
              'overflow-hidden',
              isMinimized ? 'h-auto' : 'h-[600px] max-h-[calc(100vh-48px)]'
            )}
          >
            {/* Header */}
            <div className="bg-primary-700 text-white px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <div>
                  <h3 className="font-semibold text-sm">Planning Assistant</h3>
                  <p className="text-xs text-primary-200">
                    Hampstead Renovations
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsMinimized(!isMinimized)}
                  className="p-1 hover:bg-primary-600 rounded transition-colors"
                  aria-label={isMinimized ? 'Expand' : 'Minimize'}
                >
                  <Minimize2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-primary-600 rounded transition-colors"
                  aria-label="Close"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Chat Content */}
            {!isMinimized && <ChatWindow />}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
