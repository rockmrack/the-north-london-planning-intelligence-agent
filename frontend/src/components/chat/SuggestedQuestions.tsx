'use client';

import { HelpCircle } from 'lucide-react';
import type { SuggestedQuestion } from '@/lib/api';
import { cn } from '@/lib/utils';

interface SuggestedQuestionsProps {
  questions: SuggestedQuestion[];
  onSelect: (question: string) => void;
}

export function SuggestedQuestions({
  questions,
  onSelect,
}: SuggestedQuestionsProps) {
  if (!questions || questions.length === 0) return null;

  return (
    <div className="space-y-2">
      <p className="text-xs text-neutral-500 flex items-center gap-1">
        <HelpCircle className="w-3 h-3" />
        Suggested questions
      </p>
      <div className="flex flex-wrap gap-2">
        {questions.map((q, index) => (
          <button
            key={index}
            onClick={() => onSelect(q.question)}
            className={cn(
              'text-xs px-3 py-1.5 rounded-full',
              'bg-neutral-100 text-neutral-700',
              'hover:bg-primary-100 hover:text-primary-700',
              'border border-neutral-200 hover:border-primary-200',
              'transition-colors'
            )}
          >
            {q.question}
          </button>
        ))}
      </div>
    </div>
  );
}
