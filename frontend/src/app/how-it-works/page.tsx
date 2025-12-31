'use client';

import { Header } from '@/components/ui/Header';
import { Footer } from '@/components/ui/Footer';
import { ChatWidget } from '@/components/chat/ChatWidget';

export default function HowItWorks() {
  return (
    <main className="min-h-screen bg-white">
      <Header />
      
      <div className="pt-20 pb-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-8 text-center">
            How It Works
          </h1>
          
          <div className="space-y-12">
            {/* Step 1 */}
            <div className="flex flex-col md:flex-row items-start gap-6">
              <div className="flex-shrink-0 w-16 h-16 bg-blue-700 text-white rounded-full flex items-center justify-center text-2xl font-bold">
                1
              </div>
              <div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-3">
                  Ask Your Question
                </h2>
                <p className="text-gray-600 text-lg">
                  Click the chat button and type your planning question. Whether you're wondering about extensions, loft conversions, or basement developments - just ask naturally.
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex flex-col md:flex-row items-start gap-6">
              <div className="flex-shrink-0 w-16 h-16 bg-blue-700 text-white rounded-full flex items-center justify-center text-2xl font-bold">
                2
              </div>
              <div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-3">
                  AI Searches Official Documents
                </h2>
                <p className="text-gray-600 text-lg">
                  Our AI instantly searches through thousands of pages of official planning documents from Camden, Barnet, Westminster, Brent, and Haringey councils.
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="flex flex-col md:flex-row items-start gap-6">
              <div className="flex-shrink-0 w-16 h-16 bg-blue-700 text-white rounded-full flex items-center justify-center text-2xl font-bold">
                3
              </div>
              <div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-3">
                  Get Cited Answers
                </h2>
                <p className="text-gray-600 text-lg">
                  Receive accurate, sourced answers with citations to the specific council documents. Every response references official planning policies so you know exactly where the information comes from.
                </p>
              </div>
            </div>

            {/* Step 4 */}
            <div className="flex flex-col md:flex-row items-start gap-6">
              <div className="flex-shrink-0 w-16 h-16 bg-blue-700 text-white rounded-full flex items-center justify-center text-2xl font-bold">
                4
              </div>
              <div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-3">
                  Connect With Experts
                </h2>
                <p className="text-gray-600 text-lg">
                  Need more help? Our team at Hampstead Renovations can guide you through the planning application process and help bring your project to life.
                </p>
              </div>
            </div>
          </div>

          {/* CTA */}
          <div className="mt-16 text-center">
            <p className="text-xl text-gray-600 mb-6">
              Ready to get started?
            </p>
            <button
              onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
              className="bg-blue-700 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-800 transition-colors"
            >
              Ask a Question Now
            </button>
          </div>
        </div>
      </div>

      <Footer />
      <ChatWidget />
    </main>
  );
}
