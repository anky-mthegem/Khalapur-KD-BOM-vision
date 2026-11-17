/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        office: {
          blue: "#2B579A",       // MS Word Dark Blue
          excel: "#107C41",      // MS Excel Dark Green
          gray: "#F3F2F1",       // Ribbon Background
          border: "#D2D0CE",     // Office Divider Silver
          text: "#201F1E",       // High-contrast primary text
          pass: "#107C10",       // Industrial Forest Green
          fail: "#D13438",       // Industrial Crimson Red
          progress: "#FFF4CE",   // Warning Pale Yellow
          match: "#DFF6DD",      // Exact Match Pale Green
          excluded: "#EDEBE9"    // Packaging Muted Gray
        }
      },
      fontFamily: {
        sans: ['"Segoe UI"', '-apple-system', 'BlinkMacSystemFont', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['"Cascadia Code"', 'Consolas', 'Courier New', 'monospace']
      }
    },
  },
  plugins: [],
}
