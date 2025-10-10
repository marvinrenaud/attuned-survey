/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Attuned Brand Colors
        primary: {
          DEFAULT: '#9B6B8F', // Dusty Mauve
          light: '#B88FAA',
          dark: '#7D5673',
        },
        secondary: {
          DEFAULT: '#E08B71', // Warm Coral
          light: '#F5A089',
          dark: '#C76F59',
        },
        tertiary: {
          DEFAULT: '#F5C6C0', // Soft Blush
          light: '#FFE0DC',
          dark: '#E0ACA4',
        },
        alternate: {
          DEFAULT: '#6B4C7C', // Deep Plum
          light: '#8A6A9C',
          dark: '#4F3A5C',
        },
        // Accent Colors
        accent: {
          coral: '#FF7F6E', // Energetic Coral
          sage: '#8FAA96', // Sage Green
          peach: '#FFB4A2', // Soft Peach
          sunset: '#FFA07A', // Sunset Orange
        },
        // Utility Colors
        text: {
          primary: '#2D3436', // Charcoal
          secondary: '#636E72', // Warm Gray
        },
        background: {
          primary: '#FAF8F6', // Warm White
          secondary: '#FFF5F3', // Soft Blush Background
        },
        // Semantic Colors
        success: '#7DBB9F', // Sage Success
        error: '#E67E6E', // Gentle Coral Red
        warning: '#F39C6B', // Warm Amber
        info: '#9B8FA6', // Soft Mauve Info
        
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        foreground: "hsl(var(--foreground))",
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        heading: ['Spectral', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

