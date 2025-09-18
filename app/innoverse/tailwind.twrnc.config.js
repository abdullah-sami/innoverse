// tailwind.twrnc.config.js (create this new file)
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,jsx,ts,tsx}", "./components/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        accent: "#1A8249",
        accentLight: "#79BF0D",
        bgPrimary: "#F4FFE2",
        textPrimary: "#2e2e2e",
        textSecondary: "#7D7D7D",
      },
    },
  },
  plugins: [],
  // Remove the nativewind preset for twrnc
}