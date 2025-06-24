import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        border: '#e5e7eb', // Custom border color for border-border class
        background: '#f8fafc', // light gray background
        foreground: '#1e293b', // dark slate text
        primary: {
          DEFAULT: '#2563eb', // blue-600
          foreground: '#ffffff',
        },
        secondary: {
          DEFAULT: '#f1f5f9', // slate-100
          foreground: '#1e293b',
        },
        accent: {
          DEFAULT: '#38bdf8', // sky-400
          foreground: '#ffffff',
        },
        muted: {
          DEFAULT: '#e2e8f0', // slate-200
          foreground: '#64748b', // slate-400
        },
      },
    },
  },
  plugins: [],
};

export default config; 