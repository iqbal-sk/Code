// src/index.tsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from './theme/ThemeContext';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './index.css';

const container = document.getElementById('root');
if (!container) throw new Error('Root container missing in index.html');
const root = createRoot(container);
root.render(
  <React.StrictMode>
      <ThemeProvider>
          <BrowserRouter>
              <QueryClientProvider client={new QueryClient()}>
                <App />
              </QueryClientProvider>
          </BrowserRouter>
      </ThemeProvider>

  </React.StrictMode>
);