
const { fontFamily } = require("tailwindcss/defaultTheme");

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ["var(--font-roboto-mono)", ...fontFamily.mono],
      },
      colors: {
        background: '#050505',
        core: {
          cyan: '#00E5FF',
          amber: '#FFD600',
        },
        ui: {
          highlight: 'rgba(255, 255, 255, 0.05)',
          stroke: 'rgba(255, 255, 255, 0.1)',
        },
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': {
            textShadow: '0 0 2px var(--tw-shadow-color), 0 0 4px var(--tw-shadow-color)',
            boxShadow: 'inset 0 0 3px var(--tw-shadow-color)'
          },
          '50%': {
            textShadow: '0 0 5px var(--tw-shadow-color), 0 0 10px var(--tw-shadow-color)',
            boxShadow: 'inset 0 0 5px var(--tw-shadow-color)'
          },
        },
      },
      animation: {
        pulseGlow: 'pulseGlow 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
