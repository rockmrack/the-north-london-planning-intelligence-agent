'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, Mail, ArrowRight } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { captureLead } from '@/lib/api';
import { useChatStore } from '@/lib/store';
import { cn, isValidEmail } from '@/lib/utils';

const leadSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  name: z.string().optional(),
  postcode: z.string().optional(),
  marketingConsent: z.boolean().default(false),
});

type LeadFormData = z.infer<typeof leadSchema>;

export function LeadCaptureForm() {
  const { sessionId, setUserEmail, setRequiresEmail } = useChatStore();
  const [step, setStep] = useState<'email' | 'details'>('email');

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<LeadFormData>({
    resolver: zodResolver(leadSchema),
  });

  const email = watch('email');

  const mutation = useMutation({
    mutationFn: captureLead,
    onSuccess: (response) => {
      if (response.success) {
        setUserEmail(email);
        setRequiresEmail(false);
      }
    },
  });

  const onSubmit = (data: LeadFormData) => {
    mutation.mutate({
      email: data.email,
      name: data.name,
      postcode: data.postcode,
      session_id: sessionId || undefined,
      marketing_consent: data.marketingConsent,
    });
  };

  return (
    <div className="flex flex-col h-[calc(600px-52px)] p-6">
      <div className="flex-1 flex flex-col items-center justify-center text-center">
        <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
          <Mail className="w-8 h-8 text-primary-700" />
        </div>

        <h3 className="text-lg font-semibold text-neutral-900 mb-2">
          Continue Your Research
        </h3>

        <p className="text-sm text-neutral-600 mb-6 max-w-xs">
          To continue receiving planning guidance and access detailed reports,
          please enter your email address.
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="w-full max-w-xs">
          {step === 'email' ? (
            <div className="space-y-4">
              <div>
                <input
                  type="email"
                  placeholder="Enter your email"
                  {...register('email')}
                  className={cn(
                    'input-field text-center',
                    errors.email && 'border-red-500 focus:border-red-500'
                  )}
                  autoFocus
                />
                {errors.email && (
                  <p className="text-xs text-red-500 mt-1">
                    {errors.email.message}
                  </p>
                )}
              </div>

              <button
                type="button"
                onClick={() => {
                  if (isValidEmail(email)) {
                    setStep('details');
                  }
                }}
                disabled={!email || !isValidEmail(email)}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                Continue
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-left">
                <label className="text-xs text-neutral-500 mb-1 block">
                  Email
                </label>
                <p className="text-sm text-neutral-900">{email}</p>
              </div>

              <div>
                <input
                  type="text"
                  placeholder="Your name (optional)"
                  {...register('name')}
                  className="input-field"
                />
              </div>

              <div>
                <input
                  type="text"
                  placeholder="Property postcode (optional)"
                  {...register('postcode')}
                  className="input-field"
                />
              </div>

              <div className="flex items-start gap-2">
                <input
                  type="checkbox"
                  id="marketing"
                  {...register('marketingConsent')}
                  className="mt-1"
                />
                <label
                  htmlFor="marketing"
                  className="text-xs text-neutral-600 text-left"
                >
                  I'd like to receive planning tips and updates from Hampstead
                  Renovations
                </label>
              </div>

              <button
                type="submit"
                disabled={mutation.isPending}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {mutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    Start Planning
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={() => setStep('email')}
                className="text-xs text-neutral-500 hover:text-neutral-700"
              >
                Back
              </button>
            </div>
          )}
        </form>

        {mutation.isError && (
          <p className="text-sm text-red-500 mt-4">
            Something went wrong. Please try again.
          </p>
        )}

        <p className="text-xs text-neutral-400 mt-6">
          We respect your privacy. Your data is secure.
        </p>
      </div>
    </div>
  );
}
