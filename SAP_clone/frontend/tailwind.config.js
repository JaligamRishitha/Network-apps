/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'sap-blue': '#0070f2',
        'sap-teal': '#00a1e0',
        'sap-dark': '#354a5f',
      },
    },
  },
  plugins: [],
}
