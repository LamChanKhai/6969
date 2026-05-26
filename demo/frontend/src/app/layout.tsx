import './globals.css';
import { spaceGrotesk, ibmPlexMono } from './fonts';
import { Suspense } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,
      refetchOnWindowFocus: false,
    },
  },
});

export const metadata = {
  title: 'CSCV2025 Secure Platform',
  description: 'Security Evaluation & Platform Refresh Demo',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${spaceGrotesk.variable} ${ibmPlexMono.variable}`}>
        <QueryClientProvider client={queryClient}>
          <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading...</div>}>
            {children}
          </Suspense>
        </QueryClientProvider>
      </body>
    </html>
  );
}
