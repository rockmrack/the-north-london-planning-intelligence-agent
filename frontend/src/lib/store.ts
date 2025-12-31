"use client";

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Citation, SuggestedQuestion } from './api';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: Date;
}

interface ChatState {
  // Session
  sessionId: string | null;
  setSessionId: (id: string) => void;

  // Messages
  messages: Message[];
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  clearMessages: () => void;

  // UI State
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  // Suggestions
  suggestedQuestions: SuggestedQuestion[];
  setSuggestedQuestions: (questions: SuggestedQuestion[]) => void;

  // Lead capture
  queryCount: number;
  incrementQueryCount: () => void;
  requiresEmail: boolean;
  setRequiresEmail: (requires: boolean) => void;
  userEmail: string | null;
  setUserEmail: (email: string) => void;

  // Selected borough
  selectedBorough: string | null;
  setSelectedBorough: (borough: string | null) => void;

  // Detected info
  detectedBorough: string | null;
  setDetectedBorough: (borough: string | null) => void;
  detectedLocation: string | null;
  setDetectedLocation: (location: string | null) => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      // Session
      sessionId: null,
      setSessionId: (id) => set({ sessionId: id }),

      // Messages
      messages: [],
      addMessage: (message) =>
        set((state) => ({
          messages: [
            ...state.messages,
            {
              ...message,
              id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              timestamp: new Date(),
            },
          ],
        })),
      clearMessages: () => set({ messages: [], sessionId: null, queryCount: 0 }),

      // UI State
      isOpen: false,
      setIsOpen: (open) => set({ isOpen: open }),
      isLoading: false,
      setIsLoading: (loading) => set({ isLoading: loading }),

      // Suggestions
      suggestedQuestions: [],
      setSuggestedQuestions: (questions) => set({ suggestedQuestions: questions }),

      // Lead capture
      queryCount: 0,
      incrementQueryCount: () =>
        set((state) => ({ queryCount: state.queryCount + 1 })),
      requiresEmail: false,
      setRequiresEmail: (requires) => set({ requiresEmail: requires }),
      userEmail: null,
      setUserEmail: (email) =>
        set({ userEmail: email, requiresEmail: false }),

      // Selected borough
      selectedBorough: null,
      setSelectedBorough: (borough) => set({ selectedBorough: borough }),

      // Detected info
      detectedBorough: null,
      setDetectedBorough: (borough) => set({ detectedBorough: borough }),
      detectedLocation: null,
      setDetectedLocation: (location) => set({ detectedLocation: location }),
    }),
    {
      name: 'planning-chat-store',
      partialize: (state) => ({
        sessionId: state.sessionId,
        userEmail: state.userEmail,
        queryCount: state.queryCount,
      }),
    }
  )
);
