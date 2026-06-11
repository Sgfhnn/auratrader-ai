/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        dark: { 900: '#0b0f19', 800: '#0f172a', 700: '#1e293b' },
        accent: { DEFAULT: '#3b82f6', hover: '#2563eb' },
        green: { DEFAULT: '#22c55e', muted: '#16a34a' },
        red: { DEFAULT: '#ef4444', muted: '#dc2626' },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
