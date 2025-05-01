// tailwind.config.cjs
const plugin = require('tailwindcss/plugin');

module.exports = {
  // Enable class-based dark mode (toggle via adding/removing 'dark' on <html>)
  darkMode: 'class',

  // Paths to all of your template files
  content: [
    './public/index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],

  theme: {
    extend: {
      // Custom color palette (light/dark variants)
      colors: {
        primary: {
          light: '#3b82f6',
          DEFAULT: '#2563eb',
          dark: '#1e40af',
        },
        secondary: {
          light: '#a78bfa',
          DEFAULT: '#7c3aed',
          dark: '#5b21b6',
        },
        accent: {
          light: '#fef08a',
          DEFAULT: '#fde047',
          dark: '#facc15',
        },
      },

      // Default sans font stack, can be overridden in your CSS
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },

      // Example of extending spacing & borderRadius
      spacing: {
        '72': '18rem',
        '84': '21rem',
        '96': '24rem',
      },
      borderRadius: {
        'xl': '1.5rem',
      },
    },
  },

  variants: {
    extend: {
      // Enable additional variants if needed
      backgroundColor: ['active', 'group-hover', 'dark'],
      textColor: ['active', 'dark'],
      ringWidth: ['focus-visible', 'dark'],
    },
  },

  plugins: [
    // Form styles (inputs, buttons, selects)
    require('@tailwindcss/forms'),

    // Beautiful prose defaults for markdown, blog posts, etc.
    require('@tailwindcss/typography'),

    // You can add custom utilities/base styles here
    plugin(function({ addBase, theme }) {
      addBase({
        'h1': { fontSize: theme('fontSize.3xl'), fontWeight: theme('fontWeight.bold') },
        'h2': { fontSize: theme('fontSize.2xl'), fontWeight: theme('fontWeight.semibold') },
        'h3': { fontSize: theme('fontSize.xl'),  fontWeight: theme('fontWeight.semibold') },
      });
    }),
  ],
};
