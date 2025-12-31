'use client';

import { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-sm border-b border-neutral-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <a href="/" className="flex items-center gap-2">
            <div className="w-10 h-10 bg-primary-700 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">HR</span>
            </div>
            <div className="hidden sm:block">
              <p className="font-semibold text-primary-700">Hampstead</p>
              <p className="text-xs text-neutral-500 -mt-1">Renovations</p>
            </div>
          </a>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <a
              href="/features"
              className="text-sm text-neutral-600 hover:text-primary-700 transition-colors"
            >
              Features
            </a>
            <a
              href="/coverage"
              className="text-sm text-neutral-600 hover:text-primary-700 transition-colors"
            >
              Coverage
            </a>
            <a
              href="/how-it-works"
              className="text-sm text-neutral-600 hover:text-primary-700 transition-colors"
            >
              How It Works
            </a>
            <a
              href="/contact"
              className="text-sm text-neutral-600 hover:text-primary-700 transition-colors"
            >
              Contact
            </a>
          </nav>

          {/* CTA Button */}
          <div className="hidden md:block">
            <a
              href="#chat"
              className="btn-accent text-sm"
            >
              Ask a Question
            </a>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden p-2 text-neutral-600"
            aria-label="Toggle menu"
          >
            {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden border-t border-neutral-200 bg-white">
          <nav className="container mx-auto px-4 py-4 flex flex-col gap-4">
            <a
              href="/features"
              className="text-sm text-neutral-600 hover:text-primary-700"
              onClick={() => setIsMenuOpen(false)}
            >
              Features
            </a>
            <a
              href="/coverage"
              className="text-sm text-neutral-600 hover:text-primary-700"
              onClick={() => setIsMenuOpen(false)}
            >
              Coverage
            </a>
            <a
              href="/how-it-works"
              className="text-sm text-neutral-600 hover:text-primary-700"
              onClick={() => setIsMenuOpen(false)}
            >
              How It Works
            </a>
            <a
              href="/contact"
              className="text-sm text-neutral-600 hover:text-primary-700"
              onClick={() => setIsMenuOpen(false)}
            >
              Contact
            </a>
            <a
              href="#chat"
              className="btn-accent text-sm text-center"
              onClick={() => setIsMenuOpen(false)}
            >
              Ask a Question
            </a>
          </nav>
        </div>
      )}
    </header>
  );
}
