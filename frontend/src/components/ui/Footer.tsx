'use client';

import { Mail, Phone, MapPin, Linkedin, Instagram } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-primary-700 text-white">
      {/* Main Footer */}
      <div className="container mx-auto px-4 py-12 md:py-16">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Company Info */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                <span className="text-primary-700 font-bold text-lg">HR</span>
              </div>
              <div>
                <p className="font-semibold">Hampstead</p>
                <p className="text-xs text-primary-200 -mt-1">Renovations</p>
              </div>
            </div>
            <p className="text-primary-200 text-sm mb-4">
              Award-winning architects specializing in residential renovations
              across North London.
            </p>
            <div className="flex gap-4">
              <a
                href="#"
                className="text-primary-200 hover:text-white transition-colors"
                aria-label="LinkedIn"
              >
                <Linkedin className="w-5 h-5" />
              </a>
              <a
                href="#"
                className="text-primary-200 hover:text-white transition-colors"
                aria-label="Instagram"
              >
                <Instagram className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2 text-sm text-primary-200">
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Our Services
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Portfolio
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  About Us
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Blog
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Contact
                </a>
              </li>
            </ul>
          </div>

          {/* Planning Topics */}
          <div>
            <h4 className="font-semibold mb-4">Planning Topics</h4>
            <ul className="space-y-2 text-sm text-primary-200">
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Extensions
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Loft Conversions
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Basement Development
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Conservation Areas
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Permitted Development
                </a>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-semibold mb-4">Contact Us</h4>
            <ul className="space-y-3 text-sm text-primary-200">
              <li className="flex items-center gap-2">
                <MapPin className="w-4 h-4 flex-shrink-0" />
                <span>Unit 3, Palace Court, 250 Finchley Rd, London NW3 6DN</span>
              </li>
              <li className="flex items-center gap-2">
                <Phone className="w-4 h-4 flex-shrink-0" />
                <a href="tel:+442080548756" className="hover:text-white transition-colors">
                  020 8054 8756
                </a>
              </li>
              <li className="flex items-center gap-2">
                <Mail className="w-4 h-4 flex-shrink-0" />
                <a
                  href="mailto:info@hampsteadrenovations.co.uk"
                  className="hover:text-white transition-colors"
                >
                  info@hampsteadrenovations.co.uk
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-primary-600">
        <div className="container mx-auto px-4 py-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-primary-300">
            <p>
              © {new Date().getFullYear()} Hampstead Renovations. All rights reserved.
            </p>
            <div className="flex gap-6">
              <a href="#" className="hover:text-white transition-colors">
                Privacy Policy
              </a>
              <a href="#" className="hover:text-white transition-colors">
                Terms of Service
              </a>
              <a href="#" className="hover:text-white transition-colors">
                Cookie Policy
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
