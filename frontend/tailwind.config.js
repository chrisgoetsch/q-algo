// tailwind.config.js

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        profit: '#16a34a',
        loss: '#dc2626',
        mesh: '#facc15',
        gpt: '#38bdf8',
      },
      fontFamily: {
        mono: ['Roboto Mono', 'ui-monospace', 'SFMono-Regular'],
      },
      boxShadow: {
        panel: '0 0 10px rgba(0,0,0,0.6)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
