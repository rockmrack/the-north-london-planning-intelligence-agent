'use client';

import {
  FileText,
  Search,
  MessageSquare,
  Shield,
  Zap,
  BookOpen,
} from 'lucide-react';

const features = [
  {
    icon: FileText,
    title: 'Official Document Sources',
    description:
      'Every answer is sourced from official council planning documents including Local Plans, Conservation Area Appraisals, and Design Guides.',
  },
  {
    icon: Search,
    title: 'Intelligent Search',
    description:
      'Advanced hybrid search combines semantic understanding with keyword matching to find the most relevant information for your query.',
  },
  {
    icon: MessageSquare,
    title: 'Conversational Interface',
    description:
      'Ask follow-up questions naturally. Our AI remembers your conversation context to provide coherent, helpful responses.',
  },
  {
    icon: Shield,
    title: 'Cited & Verified',
    description:
      'Every claim is backed by a citation. See exactly which document, page, and section supports each piece of advice.',
  },
  {
    icon: Zap,
    title: 'Instant Answers',
    description:
      'No more scrolling through 200-page PDFs. Get precise answers in seconds, not hours of research.',
  },
  {
    icon: BookOpen,
    title: 'Always Up-to-Date',
    description:
      'Our knowledge base is regularly updated with the latest planning guidance and policy changes from all covered councils.',
  },
];

export function Features() {
  return (
    <section id="features" className="py-16 md:py-24 bg-white">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-12 md:mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-primary-700 mb-4">
            Why Use Our Planning Assistant?
          </h2>
          <p className="text-lg text-neutral-600">
            We've built the most comprehensive AI tool for North London planning
            guidance, so you can make informed decisions about your renovation.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="group p-6 rounded-xl border border-neutral-200 hover:border-accent-400 hover:shadow-lg transition-all"
            >
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-accent-100 transition-colors">
                <feature.icon className="w-6 h-6 text-primary-700 group-hover:text-accent-500 transition-colors" />
              </div>
              <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-neutral-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
