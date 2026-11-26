module.exports = {
  content: ['./src/index.html', './src/js/**/*.js', './scripts/build.mjs'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'sans-serif'], display: ['Oswald', 'sans-serif'] },
      colors: {
        garage: {
          dark: '#121214', card: '#1B1B1E', border: '#27272A',
          steel: '#94A3B8', ice: '#F8FAFC', red: '#DC2626', redHover: '#B91C1C',
        },
      },
    },
  },
};
