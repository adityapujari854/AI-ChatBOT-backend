/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563EB',    // blue-600 for buttons, accents
        secondary: '#F3F4F6',  // gray background
        neutral: '#1e293b',    // default text color
      },
      fontFamily: {
        sans: ['Segoe UI', 'sans-serif'],
      },
      boxShadow: {
        chat: '0 1px 4px rgba(0, 0, 0, 0.08)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),  // Optional plugin for better typography utilities
  ],
};
