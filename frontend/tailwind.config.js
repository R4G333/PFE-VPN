/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Core neutrals (light enterprise console)
        canvas: "#F4F6F8",
        panel: "#FFFFFF",
        border: "#DEE3E8",
        ink: {
          900: "#1B2A4A",
          800: "#2C3E55",
          700: "#445269",
          600: "#5C6B82",
          500: "#7C8AA0",
          400: "#9DAAC0",
          300: "#C5CEDA",
          100: "#EEF1F5",
        },
        // Navy chrome (header / sidebar)
        chrome: {
          900: "#101B33",
          800: "#16243F",
          700: "#1F3258",
          600: "#2B4474",
        },
        // Severity scale
        sev: {
          critical: "#C0392B",
          high: "#E0701E",
          medium: "#E0B800",
          low: "#2D7DD2",
          info: "#7F8C9A",
        },
        ok: "#1F9D55",
        accent: "#2D7DD2",
      },
      fontFamily: {
        sans: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(16, 27, 51, 0.06), 0 1px 3px rgba(16, 27, 51, 0.04)",
      },
    },
  },
  plugins: [],
};
