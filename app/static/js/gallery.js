// Vehicle detail gallery — thumbnail click + arrow nav + keyboard.
(function () {
  const root = document.querySelector('[data-gallery]');
  if (!root) return;
  const main = root.querySelector('.gallery img');
  const counter = root.querySelector('.gallery .counter');
  const thumbs = Array.from(document.querySelectorAll('[data-gallery-thumb]'));
  if (!main || !thumbs.length) return;

  const sources = thumbs.map((t) => t.dataset.src);
  let index = 0;

  function show(i) {
    index = (i + sources.length) % sources.length;
    main.src = sources[index];
    if (counter) counter.textContent = String(index + 1).padStart(2, '0') + '/' + String(sources.length).padStart(2, '0');
    thumbs.forEach((t, j) => t.classList.toggle('is-active', j === index));
  }

  thumbs.forEach((t, i) => t.addEventListener('click', () => show(i)));
  const prev = root.querySelector('.nav.prev');
  const next = root.querySelector('.nav.next');
  prev && prev.addEventListener('click', () => show(index - 1));
  next && next.addEventListener('click', () => show(index + 1));
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') show(index - 1);
    if (e.key === 'ArrowRight') show(index + 1);
  });

  show(0);
})();
