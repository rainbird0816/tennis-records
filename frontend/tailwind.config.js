/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        court: { DEFAULT: "#1f6f43", light: "#2e8b57" }, // 코트 그린
        clay: "#c45a3b",
      },
    },
  },
  plugins: [],
};
