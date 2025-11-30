'use client';

import { ChatWidget } from '@/components/chat/ChatWidget';
import { Header } from '@/components/ui/Header';
import { Hero } from '@/components/ui/Hero';
import { Features } from '@/components/ui/Features';
import { Boroughs } from '@/components/ui/Boroughs';
import { Footer } from '@/components/ui/Footer';

export default function Home() {
  return (
    <main className="min-h-screen bg-white">
      <Header />
      <Hero />
      <Features />
      <Boroughs />
      <Footer />
      <ChatWidget />
    </main>
  );
}
