/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Deep Sea Color Palette
        'deep': {
          900: '#0a0f1a',  // Deepest background
          800: '#0a1628',  // Primary background
          700: '#0f1a2e',  // Card background
          600: '#162236',  // Elevated surface
          500: '#1e2a42',  // Border/divider
        },
        // Neon Accents
        'neon': {
          cyan: '#00d4ff',
          purple: '#a855f7',
          pink: '#f472b6',
          green: '#34d399',
          amber: '#fbbf24',
        },
        // Status colors for dark theme
        'status': {
          open: '#34d399',
          active: '#00d4ff',
          review: '#fbbf24',
          closed: '#64748b',
          idle: '#34d399',
          busy: '#f472b6',
          offline: '#64748b',
        }
      },
      fontFamily: {
        'display': ['JetBrains Mono', 'monospace'],
        'body': ['"Noto Sans SC"', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(ellipse at center, var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'deep-sea': 'linear-gradient(135deg, #0a1628 0%, #0f0a1e 50%, #1a1a3e 100%)',
        'glass': 'linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)',
      },
      boxShadow: {
        'neon-cyan': '0 0 20px rgba(0, 212, 255, 0.3), 0 0 40px rgba(0, 212, 255, 0.1)',
        'neon-purple': '0 0 20px rgba(168, 85, 247, 0.3), 0 0 40px rgba(168, 85, 247, 0.1)',
        'glass': '0 8px 32px rgba(0, 0, 0, 0.3)',
        'inner-glow': 'inset 0 1px 0 rgba(255,255,255,0.1)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 212, 255, 0.3)' },
          '100%': { boxShadow: '0 0 20px rgba(0, 212, 255, 0.5), 0 0 40px rgba(168, 85, 247, 0.3)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
    },
  },
  plugins: [],
}