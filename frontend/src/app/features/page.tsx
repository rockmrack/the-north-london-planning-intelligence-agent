'use client';

import { Header } from '@/components/ui/Header';
import { Footer } from '@/components/ui/Footer';
import { ChatWidget } from '@/components/chat/ChatWidget';
import { 
  Search, 
  FileText, 
  MapPin, 
  MessageSquare, 
  Shield, 
  Zap,
  Clock,
  CheckCircle,
  BookOpen,
  Building
} from 'lucide-react';

const features = [
  {
    icon: Search,
    title: 'Intelligent Document Search',
    description: 'Our AI searches through thousands of pages of planning documents in seconds, finding exactly what you need.',
    details: [
      'Semantic search understands context, not just keywords',
      'Searches PDFs, HTML, and Word documents',
      'OCR technology reads scanned documents',
      'Cross-references multiple council sources'
    ]
  },
  {
    icon: MapPin,
    title: 'Location-Aware Guidance',
    description: 'Get advice specific to your exact location, including conservation areas and special planning zones.',
    details: [
      'Automatic postcode detection',
      'Conservation area mapping',
      'Listed building identification',
      'Local policy zone awareness'
    ]
  },
  {
    icon: FileText,
    title: 'Cited Responses',
    description: 'Every answer comes with citations to official council documents so you can verify the information.',
    details: [
      'Direct links to source documents',
      'Page and section references',
      'Document date tracking',
      'Multiple source verification'
    ]
  },
  {
    icon: MessageSquare,
    title: 'Conversational Interface',
    description: 'Ask questions naturally, just like talking to a planning expert. Follow up and dig deeper.',
    details: [
      'Natural language understanding',
      'Multi-turn conversations',
      'Context retention across questions',
      'Suggested follow-up questions'
    ]
  },
  {
    icon: Shield,
    title: 'Enterprise Security',
    description: 'Your data is protected with bank-grade security. We never share your information.',
    details: [
      'End-to-end encryption',
      'GDPR compliant',
      'No data sharing with third parties',
      'Secure cloud infrastructure'
    ]
  },
  {
    icon: Zap,
    title: 'Instant Responses',
    description: 'Get answers in seconds, not days. No more waiting for council callbacks or searching through PDFs.',
    details: [
      'Sub-second search results',
      'Real-time AI processing',
      '24/7 availability',
      'No appointment needed'
    ]
  },
  {
    icon: Clock,
    title: 'Always Up-to-Date',
    description: 'Our document database is regularly updated with the latest planning policies and guidelines.',
    details: [
      'Regular document updates',
      'New policy alerts',
      'Historical document access',
      'Change tracking'
    ]
  },
  {
    icon: BookOpen,
    title: 'Comprehensive Coverage',
    description: 'From permitted development to full planning applications, we cover all aspects of planning.',
    details: [
      'Permitted development rights',
      'Planning application requirements',
      'Building regulations guidance',
      'Appeal process information'
    ]
  }
];

export default function Features() {
  return (
    <main className="min-h-screen bg-white">
      <Header />
      
      <div className="pt-20 pb-16">
        {/* Hero Section */}
        <div className="bg-gradient-to-b from-blue-50 to-white py-16">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
              Powerful Features for <span className="text-blue-700">Smarter Planning</span>
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our AI-powered platform combines cutting-edge technology with comprehensive planning knowledge to give you the answers you need, instantly.
            </p>
          </div>
        </div>

        {/* Features Grid */}
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="grid md:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="bg-white border border-gray-200 rounded-2xl p-8 hover:shadow-lg transition-shadow"
              >
                <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center mb-6">
                  <feature.icon className="w-7 h-7 text-blue-700" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-600 mb-4">
                  {feature.description}
                </p>
                <ul className="space-y-2">
                  {feature.details.map((detail, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-500">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      {detail}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-blue-700 py-16">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-3xl font-bold text-white mb-4">
              Ready to experience these features?
            </h2>
            <p className="text-blue-100 text-lg mb-8">
              Try our Planning Assistant now - it's free to ask your first questions.
            </p>
            <a 
              href="/"
              className="inline-block bg-white text-blue-700 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-50 transition-colors"
            >
              Start Asking Questions
            </a>
          </div>
        </div>
      </div>

      <Footer />
      <ChatWidget />
    </main>
  );
}
