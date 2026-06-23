import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        canvas: "#f5f7fa",
        line: "#dbe1e8",
        teal: {
          50: "#edfafa",
          100: "#d5f3f1",
          500: "#159a93",
          600: "#0f7f79",
          700: "#116762"
        },
      },
      boxShadow: {
        panel: "0 1px 2px rgba(23, 32, 51, 0.04), 0 8px 24px rgba(23, 32, 51, 0.04)",
      },
    },
  },
  plugins: [],
};

export default config;
