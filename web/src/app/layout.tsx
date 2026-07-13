import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import AppShell from '@/components/AppShell';

const geist = Geist({ subsets: ['latin'], variable: '--font-geist' });
const geistMono = Geist_Mono({ subsets: ['latin'], variable: '--font-geist-mono' });

export const metadata: Metadata = {
  title: 'IPL Sim — Cricket Simulation Terminal',
  description: 'A ball-by-ball T20 cricket simulation engine on real Cricsheet data.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geist.variable} ${geistMono.variable}`}>
      <body className="min-h-screen antialiased selection:bg-[#33E1C6] selection:text-[#04120F]">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
