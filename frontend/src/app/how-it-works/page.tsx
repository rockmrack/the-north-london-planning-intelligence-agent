'use client';

import { Header } from '@/components/ui/Header';
import { Footer } from '@/components/ui/Footer';
import { ChatWidget } from '@/components/chat/ChatWidget';
import { 
  MessageSquare, 
  Search, 
  FileCheck, 
  Users, 
  Clock,
  Shield,
  Sparkles,
  ArrowRight,
  CheckCircle,
  Zap,
  FileText,
  Building,
  HelpCircle,
  Lightbulb,
  Target,
  Award
} from 'lucide-react';

const steps = [
  {
    number: 1,
    icon: MessageSquare,
    title: 'Ask Your Planning Question',
    subtitle: 'Natural Language, Zero Jargon',
    description: 'Click the chat button in the corner and ask anything about UK planning permission. Our AI understands everyday language - no need to know technical terms.',
    examples: [
      '"Can I build a loft extension in Camden?"',
      '"Do I need planning permission for a garage conversion?"',
      '"What are the rules for garden buildings in Hampstead?"',
      '"How close can I build to my boundary?"'
    ],
    color: 'blue',
    tips: [
      'Include your postcode or area for location-specific answers',
      'Be specific about what you want to build',
      'Ask follow-up questions to dig deeper'
    ]
  },
  {
    number: 2,
    icon: Search,
    title: 'AI Searches Official Documents',
    subtitle: 'Thousands of Pages in Milliseconds',
    description: 'Our advanced AI instantly searches through 11,400+ official planning documents from 5 North London councils. It finds the exact policies relevant to your question.',
    stats: [
      { label: 'Documents Searched', value: '11,400+' },
      { label: 'Response Time', value: '<3 sec' },
      { label: 'Councils Covered', value: '5' },
      { label: 'Accuracy Rate', value: '95%+' }
    ],
    color: 'purple',
    techDetails: [
      'Semantic search understands context, not just keywords',
      'Vector embeddings find conceptually related content',
      'Cross-references multiple document sources',
      'OCR reads scanned PDFs and images'
    ]
  },
  {
    number: 3,
    icon: FileCheck,
    title: 'Get Cited, Verified Answers',
    subtitle: 'Every Fact Has a Source',
    description: 'Receive comprehensive answers backed by official council documents. Every claim is cited so you can verify the information and trust what you read.',
    features: [
      {
        icon: FileText,
        title: 'Direct Citations',
        text: 'Links to the exact document and section'
      },
      {
        icon: Shield,
        title: 'Verified Sources',
        text: 'Only official council documents used'
      },
      {
        icon: Clock,
        title: 'Up-to-Date',
        text: 'Documents updated weekly'
      },
      {
        icon: Target,
        title: 'Location-Specific',
        text: 'Tailored to your exact area'
      }
    ],
    color: 'green'
  },
  {
    number: 4,
    icon: Users,
    title: 'Connect With Experts',
    subtitle: 'Human Help When You Need It',
    description: "Need professional guidance? Our team at Hampstead Renovations specialises in North London planning. From initial consultation to approved plans, we're here to help.",
    services: [
      'Pre-application advice',
      'Planning application preparation',
      'Architectural drawings',
      'Planning appeals support',
      'Project management',
      'Building regulations applications'
    ],
    color: 'orange'
  }
];

const faqs = [
  {
    question: 'Is this service free?',
    answer: 'Yes! Asking questions to our AI planning assistant is completely free. There are no hidden fees or subscriptions required.'
  },
  {
    question: 'How accurate are the answers?',
    answer: 'Our AI achieves 95%+ accuracy by citing official council documents. Every answer includes sources so you can verify the information.'
  },
  {
    question: 'Which areas do you cover?',
    answer: 'We cover 5 North London boroughs: Camden, Barnet, Westminster, Brent, and Haringey. More areas coming soon!'
  },
  {
    question: 'Can I trust the advice for my application?',
    answer: 'Our AI provides guidance based on official planning policies, but for formal applications we recommend consulting with a planning professional. Our team can help with that!'
  },
  {
    question: 'How up-to-date is the information?',
    answer: 'We update our document database weekly to ensure you always get the most current planning policies and guidance.'
  },
  {
    question: 'What if I need help beyond the chatbot?',
    answer: 'Our team at Hampstead Renovations offers professional planning services. Just leave your details in the contact form or ask the chatbot to connect you with an expert.'
  }
];

const benefits = [
  { icon: Zap, title: 'Instant Answers', text: 'Get responses in seconds, not days' },
  { icon: Shield, title: 'Trusted Sources', text: '100% official council documents' },
  { icon: Clock, title: 'Available 24/7', text: 'Ask questions any time of day' },
  { icon: Award, title: 'Free to Use', text: 'No subscription or payment required' }
];

export default function HowItWorks() {
  return (
    <main className="min-h-screen bg-white">
      <Header />
      
      <div className="pt-20 pb-16">
        {/* Hero Section */}
        <div className="bg-gradient-to-br from-blue-50 via-purple-50 to-green-50 py-20">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Sparkles className="w-4 h-4" />
              AI-Powered Planning Assistance
            </div>
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Planning Permission Made <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">Simple</span>
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-10">
              From question to answer in seconds. Our AI searches thousands of official planning documents so you don't have to.
            </p>
            
            {/* Benefits Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
              {benefits.map((benefit, index) => (
                <div key={index} className="bg-white/80 backdrop-blur-sm rounded-xl p-4 text-center">
                  <benefit.icon className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                  <div className="font-semibold text-gray-900 text-sm">{benefit.title}</div>
                  <div className="text-gray-500 text-xs">{benefit.text}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Steps Section */}
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Four simple steps from question to answer. No sign-up required, no waiting, no complicated forms.
            </p>
          </div>

          <div className="space-y-24">
            {/* Step 1 */}
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 bg-blue-600 text-white rounded-2xl flex items-center justify-center">
                    <MessageSquare className="w-8 h-8" />
                  </div>
                  <div>
                    <div className="text-blue-600 font-semibold text-sm">Step 1</div>
                    <h3 className="text-2xl font-bold text-gray-900">Ask Your Planning Question</h3>
                  </div>
                </div>
                <p className="text-gray-600 text-lg mb-6">
                  Click the chat button in the corner and ask anything about UK planning permission. Our AI understands everyday language - no need to know technical terms.
                </p>
                <div className="bg-blue-50 rounded-xl p-6 mb-6">
                  <div className="text-sm font-semibold text-blue-700 mb-3 flex items-center gap-2">
                    <Lightbulb className="w-4 h-4" />
                    Example Questions
                  </div>
                  <div className="space-y-2">
                    {steps[0].examples?.map((example, i) => (
                      <div key={i} className="bg-white rounded-lg px-4 py-2 text-gray-700 text-sm border border-blue-100">
                        {example}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  {steps[0].tips?.map((tip, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm text-gray-600">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      {tip}
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-gradient-to-br from-blue-100 to-blue-200 rounded-2xl p-8 relative">
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                      <MessageSquare className="w-5 h-5 text-white" />
                    </div>
                    <div className="font-semibold text-gray-900">Planning Assistant</div>
                  </div>
                  <div className="space-y-3">
                    <div className="bg-gray-100 rounded-lg p-3 text-sm text-gray-700">
                      Can I build a loft extension on my Victorian terrace in Hampstead?
                    </div>
                    <div className="bg-blue-50 rounded-lg p-3 text-sm text-gray-700">
                      Based on Camden's planning policies, Victorian terraces in Hampstead typically allow rear dormer extensions under permitted development...
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 2 */}
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div className="order-2 md:order-1 bg-gradient-to-br from-purple-100 to-purple-200 rounded-2xl p-8">
                <div className="grid grid-cols-2 gap-4">
                  {steps[1].stats?.map((stat, i) => (
                    <div key={i} className="bg-white rounded-xl p-4 text-center shadow-sm">
                      <div className="text-2xl font-bold text-purple-600">{stat.value}</div>
                      <div className="text-xs text-gray-500">{stat.label}</div>
                    </div>
                  ))}
                </div>
                <div className="mt-6 bg-white/80 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Search className="w-4 h-4 text-purple-600" />
                    <span className="text-sm font-medium text-gray-700">Searching documents...</span>
                  </div>
                  <div className="h-2 bg-purple-100 rounded-full overflow-hidden">
                    <div className="h-full w-3/4 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full animate-pulse" />
                  </div>
                </div>
              </div>
              <div className="order-1 md:order-2">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 bg-purple-600 text-white rounded-2xl flex items-center justify-center">
                    <Search className="w-8 h-8" />
                  </div>
                  <div>
                    <div className="text-purple-600 font-semibold text-sm">Step 2</div>
                    <h3 className="text-2xl font-bold text-gray-900">AI Searches Official Documents</h3>
                  </div>
                </div>
                <p className="text-gray-600 text-lg mb-6">
                  Our advanced AI instantly searches through 11,400+ official planning documents from 5 North London councils. It finds the exact policies relevant to your question.
                </p>
                <div className="space-y-3">
                  {steps[1].techDetails?.map((detail, i) => (
                    <div key={i} className="flex items-start gap-3 bg-purple-50 rounded-lg p-3">
                      <CheckCircle className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{detail}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Step 3 */}
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 bg-green-600 text-white rounded-2xl flex items-center justify-center">
                    <FileCheck className="w-8 h-8" />
                  </div>
                  <div>
                    <div className="text-green-600 font-semibold text-sm">Step 3</div>
                    <h3 className="text-2xl font-bold text-gray-900">Get Cited, Verified Answers</h3>
                  </div>
                </div>
                <p className="text-gray-600 text-lg mb-6">
                  Receive comprehensive answers backed by official council documents. Every claim is cited so you can verify the information and trust what you read.
                </p>
                <div className="grid grid-cols-2 gap-4">
                  {steps[2].features?.map((feature, i) => (
                    <div key={i} className="bg-green-50 rounded-xl p-4">
                      <feature.icon className="w-6 h-6 text-green-600 mb-2" />
                      <div className="font-semibold text-gray-900 text-sm">{feature.title}</div>
                      <div className="text-gray-600 text-xs">{feature.text}</div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-gradient-to-br from-green-100 to-green-200 rounded-2xl p-8">
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <div className="text-sm text-gray-700 mb-4">
                    Under <span className="font-semibold">Camden's Supplementary Planning Document (SPD)</span> for residential extensions, rear dormers on Victorian terraces are generally permitted under Class B...
                  </div>
                  <div className="border-t pt-4">
                    <div className="text-xs text-gray-500 mb-2">Sources:</div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-xs bg-green-50 rounded px-3 py-2">
                        <FileText className="w-3 h-3 text-green-600" />
                        <span className="text-gray-700">Camden Residential Design Guide 2023</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs bg-green-50 rounded px-3 py-2">
                        <FileText className="w-3 h-3 text-green-600" />
                        <span className="text-gray-700">Hampstead Conservation Area Appraisal</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 4 */}
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div className="order-2 md:order-1 bg-gradient-to-br from-orange-100 to-orange-200 rounded-2xl p-8">
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-orange-600 rounded-xl flex items-center justify-center">
                      <Building className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <div className="font-bold text-gray-900">Hampstead Renovations</div>
                      <div className="text-sm text-gray-500">Planning & Design Experts</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {steps[3].services?.map((service, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-gray-600">
                        <CheckCircle className="w-3 h-3 text-orange-500" />
                        {service}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="order-1 md:order-2">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 bg-orange-600 text-white rounded-2xl flex items-center justify-center">
                    <Users className="w-8 h-8" />
                  </div>
                  <div>
                    <div className="text-orange-600 font-semibold text-sm">Step 4</div>
                    <h3 className="text-2xl font-bold text-gray-900">Connect With Experts</h3>
                  </div>
                </div>
                <p className="text-gray-600 text-lg mb-6">
                  Need professional guidance? Our team at Hampstead Renovations specialises in North London planning. From initial consultation to approved plans, we're here to help.
                </p>
                <a 
                  href="/contact"
                  className="inline-flex items-center gap-2 bg-orange-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-orange-700 transition-colors"
                >
                  Contact Our Team
                  <ArrowRight className="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="bg-gray-50 py-20">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <div className="inline-flex items-center gap-2 text-blue-600 mb-4">
                <HelpCircle className="w-5 h-5" />
                <span className="font-semibold">FAQ</span>
              </div>
              <h2 className="text-3xl font-bold text-gray-900">Frequently Asked Questions</h2>
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              {faqs.map((faq, index) => (
                <div key={index} className="bg-white rounded-xl p-6 shadow-sm">
                  <h3 className="font-semibold text-gray-900 mb-2">{faq.question}</h3>
                  <p className="text-gray-600 text-sm">{faq.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 py-20">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              Ready to ask your planning question?
            </h2>
            <p className="text-blue-100 text-lg mb-8 max-w-2xl mx-auto">
              Join thousands of homeowners who've used our AI to understand planning rules. It's free, instant, and backed by official council documents.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a 
                href="/"
                className="inline-flex items-center justify-center gap-2 bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-50 transition-colors"
              >
                <MessageSquare className="w-5 h-5" />
                Start Asking Questions
              </a>
              <a 
                href="/contact"
                className="inline-flex items-center justify-center gap-2 bg-transparent border-2 border-white text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-white/10 transition-colors"
              >
                <Users className="w-5 h-5" />
                Talk to an Expert
              </a>
            </div>
          </div>
        </div>
      </div>

      <Footer />
      <ChatWidget />
    </main>
  );
}
