'use client';

import { MapPin, CheckCircle } from 'lucide-react';

const boroughs = [
  {
    name: 'Camden',
    areas: ['Hampstead', 'Belsize Park', 'Primrose Hill', 'Gospel Oak'],
    highlights: ['40+ Conservation Areas', 'Extensive basement guidance'],
    color: 'bg-blue-500',
  },
  {
    name: 'Barnet',
    areas: ['Finchley', 'Golders Green', 'Hendon', 'Mill Hill'],
    highlights: ['Residential design guides', 'Sustainability SPD'],
    color: 'bg-green-500',
  },
  {
    name: 'Westminster',
    areas: ['Marylebone', 'Mayfair', 'Fitzrovia', 'St Johns Wood'],
    highlights: ['City Plan 2019-2040', 'Basement development SPD'],
    color: 'bg-purple-500',
  },
  {
    name: 'Brent',
    areas: ['Wembley', 'Willesden', 'Kilburn', 'Neasden'],
    highlights: ['Householder design guide', 'Local Plan'],
    color: 'bg-orange-500',
  },
  {
    name: 'Haringey',
    areas: ['Highgate', 'Crouch End', 'Muswell Hill', 'Hornsey'],
    highlights: ['Extension guidelines', 'Conservation guidance'],
    color: 'bg-red-500',
  },
];

export function Boroughs() {
  return (
    <section id="boroughs" className="py-16 md:py-24 bg-neutral-50">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-12 md:mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-primary-700 mb-4">
            Coverage Across North London
          </h2>
          <p className="text-lg text-neutral-600">
            Our AI has been trained on planning documents from five key North
            London boroughs, covering hundreds of conservation areas and
            thousands of pages of guidance.
          </p>
        </div>

        {/* Boroughs Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {boroughs.map((borough, index) => (
            <div
              key={index}
              className="bg-white rounded-xl p-6 border border-neutral-200 hover:shadow-lg transition-shadow"
            >
              {/* Borough Header */}
              <div className="flex items-center gap-3 mb-4">
                <div
                  className={`w-3 h-3 rounded-full ${borough.color}`}
                ></div>
                <h3 className="text-xl font-semibold text-neutral-900">
                  {borough.name}
                </h3>
              </div>

              {/* Areas */}
              <div className="mb-4">
                <p className="text-sm text-neutral-500 mb-2">Key Areas:</p>
                <div className="flex flex-wrap gap-2">
                  {borough.areas.map((area, i) => (
                    <span
                      key={i}
                      className="text-xs bg-neutral-100 text-neutral-700 px-2 py-1 rounded"
                    >
                      <MapPin className="w-3 h-3 inline mr-1" />
                      {area}
                    </span>
                  ))}
                </div>
              </div>

              {/* Highlights */}
              <div>
                <p className="text-sm text-neutral-500 mb-2">Document Coverage:</p>
                <ul className="space-y-1">
                  {borough.highlights.map((highlight, i) => (
                    <li
                      key={i}
                      className="text-sm text-neutral-700 flex items-center gap-2"
                    >
                      <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                      {highlight}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}

          {/* Coming Soon Card */}
          <div className="bg-neutral-100 rounded-xl p-6 border border-dashed border-neutral-300 flex flex-col items-center justify-center text-center">
            <div className="w-12 h-12 bg-neutral-200 rounded-full flex items-center justify-center mb-3">
              <MapPin className="w-6 h-6 text-neutral-400" />
            </div>
            <h3 className="font-semibold text-neutral-700 mb-2">More Coming Soon</h3>
            <p className="text-sm text-neutral-500">
              We're expanding coverage to additional London boroughs.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
