/** @type {import('tailwindcss').Config} */
module.exports = {
  
  content: ["./app/**/*.{js,jsx,ts,tsx}", "./components/**/*.{js,jsx,ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        accent: "#1A8249",
        accentLight: "#79BF0D",
        bgPrimary: "#F4FFE2",
        textPrimary: "#ff0202ff",
        textSecondary: "#7D7D7D",
        

      },
    },
  },
  plugins: [],
}