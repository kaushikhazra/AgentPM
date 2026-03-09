import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/providers/AuthProvider';
import { ThemeProvider } from '@/providers/ThemeProvider';
import { TimerProvider } from '@/providers/TimerProvider';
import { ModalProvider } from '@/providers/ModalProvider';
import { ToastProvider } from '@/providers/ToastProvider';
import { DataRefreshProvider } from '@/providers/DataRefreshProvider';
import { routes } from '@/routes';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
    },
  },
});

const router = createBrowserRouter(routes);

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <DataRefreshProvider>
        <ThemeProvider>
          <AuthProvider>
            <ToastProvider>
              <TimerProvider>
                <ModalProvider>
                  <RouterProvider router={router} />
                </ModalProvider>
              </TimerProvider>
            </ToastProvider>
          </AuthProvider>
        </ThemeProvider>
      </DataRefreshProvider>
    </QueryClientProvider>
  );
}
