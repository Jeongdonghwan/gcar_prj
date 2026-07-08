// Hero banner auto-rotation (5s).
(function () {
  const slides = document.querySelectorAll('[data-hero-slide]');
  const counter = document.querySelector('[data-hero-counter]');
  if (slides.length < 2) return;
  let i = 0;
  function show(n) {
    i = (n + slides.length) % slides.length;
    slides.forEach((s, j) => s.style.display = j === i ? '' : 'none');
    if (counter) counter.textContent = (i + 1) + '/' + slides.length;
  }
  show(0);
  setInterval(() => show(i + 1), 5000);
})();
