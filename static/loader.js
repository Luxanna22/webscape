// Get the loader and playground elements
const loader = document.querySelector('.loader');
const playground = document.querySelector('.playground');

// Add a delay before hiding the loader and showing the playground
setTimeout(() => {
  loader.style.display = 'none';
  playground.style.display = 'block';
}, 2000); // 2000ms = 2 seconds