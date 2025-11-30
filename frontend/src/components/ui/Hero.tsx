'use client';

import { ArrowRight, CheckCircle } from 'lucide-react';
import { useChatStore } from '@/lib/store';

export function Hero() {
  const { setIsOpen } = useChatStore();

  const features = [
    'Instant answers from official planning documents',
    'Coverage across 5 North London boroughs',
    'Cited sources you can trust',
  ];

  return (
    <section className="pt-24 pb-16 md:pt-32 md:pb-24 bg-gradient-to-b from-primary-50 to-white">
      <div className="container mx-auto px-4">
        <div className="max-w-3xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-accent-100 text-accent-600 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
            <span className="w-2 h-2 bg-accent-400 rounded-full animate-pulse"></span>
            AI-Powered Planning Guidance
          </div>

          {/* Headline */}
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-primary-700 mb-6 leading-tight">
            Planning Permission
            <br />
            <span className="text-accent-400">Made Simple</span>
          </h1>

          {/* Subheadline */}
          <p className="text-lg md:text-xl text-neutral-600 mb-8 max-w-2xl mx-auto">
            Get instant, cited answers about UK planning permission for your
            renovation project. Our AI has analyzed thousands of pages of
            official council documents.
          </p>

          {/* Features List */}
          <div className="flex flex-wrap justify-center gap-4 mb-10">
            {features.map((feature, index) => (
              <div
                key={index}
                className="flex items-center gap-2 text-sm text-neutral-700"
              >
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>{feature}</span>
              </div>
            ))}
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => setIsOpen(true)}
              className="btn-primary text-lg px-8 py-3 flex items-center gap-2 group"
            >
              Ask a Planning Question
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <a
              href="#how-it-works"
              className="btn-secondary text-lg px-8 py-3"
            >
              See How It Works
            </a>
          </div>

          {/* Trust Signals */}
          <div className="mt-12 pt-8 border-t border-neutral-200">
            <p className="text-sm text-neutral-500 mb-4">
              Trusted by homeowners and architects across North London
            </p>
            <div className="flex flex-wrap justify-center gap-8 text-neutral-400">
              <div className="text-center">
                <p className="text-2xl font-bold text-primary-700">5</p>
                <p className="text-xs">Boroughs Covered</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-primary-700">1000+</p>
                <p className="text-xs">Documents Analyzed</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-primary-700">24/7</p>
                <p className="text-xs">Available</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
