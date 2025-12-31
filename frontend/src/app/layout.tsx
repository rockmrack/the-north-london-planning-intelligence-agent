import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'North London Planning Intelligence Agent | Hampstead Renovations',
  description:
    'AI-powered planning permission guidance for Camden, Barnet, Westminster, Brent, and Haringey. Get instant, cited answers from official council documents.',
  metadataBase:
    process.env.NEXT_PUBLIC_SITE_URL
      ? new URL(process.env.NEXT_PUBLIC_SITE_URL)
      : undefined,
  keywords: [
    'planning permission',
    'London planning',
    'Camden planning',
    'Barnet planning',
    'Westminster planning',
    'conservation area',
    'permitted development',
    'house extension',
    'loft conversion',
    'basement development',
  ],
  authors: [{ name: 'Hampstead Renovations' }],
  openGraph: {
    title: 'North London Planning Intelligence Agent',
    description: 'AI-powered planning permission guidance for North London',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
