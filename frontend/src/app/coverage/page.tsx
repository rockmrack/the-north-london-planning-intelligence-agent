'use client';

import { Header } from '@/components/ui/Header';
import { Footer } from '@/components/ui/Footer';
import { ChatWidget } from '@/components/chat/ChatWidget';
import { MapPin, CheckCircle, FileText, Building } from 'lucide-react';

const boroughs = [
  {
    name: 'Camden',
    description: 'Including Hampstead, Belsize Park, Primrose Hill, and Kings Cross',
    color: 'bg-blue-600',
    stats: { documents: '2,500+', policies: '150+', updates: 'Weekly' },
    areas: ['Hampstead', 'Belsize Park', 'Primrose Hill', 'Kings Cross', 'Kentish Town', 'Gospel Oak', 'Swiss Cottage'],
    highlights: [
      'Extensive conservation area coverage',
      'Hampstead Heath protection zones',
      'Basement development policies',
      'Shop front guidelines'
    ]
  },
  {
    name: 'Barnet',
    description: 'Including Finchley, Hendon, Edgware, and Mill Hill',
    color: 'bg-green-600',
    stats: { documents: '2,200+', policies: '130+', updates: 'Weekly' },
    areas: ['Finchley', 'Hendon', 'Edgware', 'Mill Hill', 'Golders Green', 'Barnet', 'Totteridge'],
    highlights: [
      'Green Belt regulations',
      'Character area appraisals',
      'Residential design guidance',
      'Tree preservation orders'
    ]
  },
  {
    name: 'Westminster',
    description: 'Including Marylebone, Mayfair, Pimlico, and Paddington',
    color: 'bg-purple-600',
    stats: { documents: '3,000+', policies: '200+', updates: 'Weekly' },
    areas: ['Marylebone', 'Mayfair', 'Pimlico', 'Paddington', 'Victoria', 'Soho', 'Fitzrovia'],
    highlights: [
      'Listed building expertise',
      'Royal Parks buffer zones',
      'Central Activities Zone policies',
      'Heritage at Risk guidance'
    ]
  },
  {
    name: 'Brent',
    description: 'Including Wembley, Kilburn, Willesden, and Harlesden',
    color: 'bg-orange-600',
    stats: { documents: '1,800+', policies: '110+', updates: 'Weekly' },
    areas: ['Wembley', 'Kilburn', 'Willesden', 'Harlesden', 'Neasden', 'Kingsbury', 'Queensbury'],
    highlights: [
      'Wembley regeneration area',
      'Housing zone policies',
      'Tall buildings guidance',
      'Industrial land policies'
    ]
  },
  {
    name: 'Haringey',
    description: 'Including Crouch End, Muswell Hill, Highgate, and Tottenham',
    color: 'bg-red-600',
    stats: { documents: '1,900+', policies: '120+', updates: 'Weekly' },
    areas: ['Crouch End', 'Muswell Hill', 'Highgate', 'Tottenham', 'Hornsey', 'Wood Green', 'Alexandra Palace'],
    highlights: [
      'Highgate conservation expertise',
      'Tottenham regeneration',
      'Victorian/Edwardian terraces',
      'Shopfront design codes'
    ]
  }
];

export default function Coverage() {
  return (
    <main className="min-h-screen bg-white">
      <Header />
      
      <div className="pt-20 pb-16">
        {/* Hero Section */}
        <div className="bg-gradient-to-b from-green-50 to-white py-16">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
              North London <span className="text-green-700">Coverage</span>
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
              Our AI has been trained on planning documents from 5 North London boroughs, covering hundreds of neighborhoods and thousands of policies.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              {boroughs.map((borough) => (
                <span 
                  key={borough.name}
                  className={`${borough.color} text-white px-4 py-2 rounded-full text-sm font-medium`}
                >
                  {borough.name}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="bg-gray-900 py-8">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-3xl md:text-4xl font-bold text-white">11,400+</div>
                <div className="text-gray-400 text-sm">Documents Indexed</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-bold text-white">710+</div>
                <div className="text-gray-400 text-sm">Planning Policies</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-bold text-white">5</div>
                <div className="text-gray-400 text-sm">Boroughs Covered</div>
              </div>
              <div>
                <div className="text-3xl md:text-4xl font-bold text-white">Weekly</div>
                <div className="text-gray-400 text-sm">Document Updates</div>
              </div>
            </div>
          </div>
        </div>

        {/* Borough Cards */}
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            Detailed Borough Coverage
          </h2>
          
          <div className="space-y-8">
            {boroughs.map((borough, index) => (
              <div 
                key={borough.name}
                className="bg-white border border-gray-200 rounded-2xl overflow-hidden hover:shadow-lg transition-shadow"
              >
                <div className={`${borough.color} px-6 py-4`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <MapPin className="w-6 h-6 text-white" />
                      <h3 className="text-2xl font-bold text-white">{borough.name}</h3>
                    </div>
                    <div className="flex gap-4 text-white/90 text-sm">
                      <span>{borough.stats.documents} docs</span>
                      <span>{borough.stats.policies} policies</span>
                    </div>
                  </div>
                  <p className="text-white/80 mt-1">{borough.description}</p>
                </div>
                
                <div className="p-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Areas Covered */}
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <Building className="w-4 h-4" />
                        Areas Covered
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {borough.areas.map((area) => (
                          <span 
                            key={area}
                            className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm"
                          >
                            {area}
                          </span>
                        ))}
                      </div>
                    </div>
                    
                    {/* Key Highlights */}
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        Policy Highlights
                      </h4>
                      <ul className="space-y-2">
                        {borough.highlights.map((highlight, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                            <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                            {highlight}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-green-700 py-16">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-3xl font-bold text-white mb-4">
              Find your area's planning rules
            </h2>
            <p className="text-green-100 text-lg mb-8">
              Just tell us your postcode or area and we'll find the relevant policies.
            </p>
            <a 
              href="/"
              className="inline-block bg-white text-green-700 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-green-50 transition-colors"
            >
              Ask About Your Area
            </a>
          </div>
        </div>
      </div>

      <Footer />
      <ChatWidget />
    </main>
  );
}
