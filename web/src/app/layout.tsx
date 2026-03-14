import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Navbar from '@/components/Navbar';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'IPL Analytics Dashboard | ESPN Style',
  description: 'Phase 8 — Premium Dark Theme Match & Tournament Simulator',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} min-h-screen flex flex-col antialiased selection:bg-[#1E88E5] selection:text-white`}>
        <Navbar />
        <main className="flex-1 w-full max-w-[1400px] mx-auto p-4 md:p-6 lg:p-8">
          {children}
        </main>
      </body>
    </html>
  );
}
