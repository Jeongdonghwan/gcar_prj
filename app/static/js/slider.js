// Vehicle slider — 2 rows × N columns laid out via CSS Grid, transformed horizontally.
// Per-page card count: tablet (768~1023) = 4 (2×2), PC (≥1024) = 8 (4×2). Mobile: no transform.
//
// Markup contract:
//   <section data-vehicle-slider>
//     ... optional [data-slider-prev], [data-slider-next], [data-slider-counter] ...
//     <div class="vehicle-slider-wrap">
//       <div class="vehicle-slider-track"> ...cards... </div>
//     </div>
//     ... optional [data-slider-pager] ...
//   </section>
(function () {
  function pageColumnsFor() {
    if (window.matchMedia('(min-width: 1024px)').matches) return 4;
    if (window.matchMedia('(min-width: 768px)').matches) return 2;
    return 1;
  }

  function init(root) {
    const wrap = root.querySelector('.vehicle-slider-wrap');
    const track = wrap && wrap.querySelector('.vehicle-slider-track');
    if (!wrap || !track) return;
    const prev = root.querySelector('[data-slider-prev]');
    const next = root.querySelector('[data-slider-next]');
    const counter = root.querySelector('[data-slider-counter]');
    const pager = root.querySelector('[data-slider-pager]');

    const rows = root.classList.contains('is-single-row') ? 1 : 2;

    let pageIndex = 0;
    let totalPages = 1;

    function compute() {
      const cols = pageColumnsFor();
      const total = track.children.length;

      if (cols === 1) {
        track.style.transform = '';
        totalPages = 1;
        if (counter) counter.textContent = '';
        if (prev) prev.disabled = true;
        if (next) next.disabled = true;
        renderPager(1);
        return;
      }

      const columnsTotal = Math.ceil(total / rows);
      totalPages = Math.max(1, Math.ceil(columnsTotal / cols));
      pageIndex = Math.min(pageIndex, totalPages - 1);
      renderPager(totalPages);
      apply();
    }

    function apply() {
      const gap = 20;
      const width = wrap.clientWidth;
      const shift = (width + gap) * pageIndex;
      track.style.transform = `translateX(-${shift}px)`;
      if (counter) counter.textContent = `${pageIndex + 1}/${totalPages}`;
      if (prev) prev.disabled = pageIndex === 0;
      if (next) next.disabled = pageIndex >= totalPages - 1;
      if (pager) {
        pager.querySelectorAll('.num').forEach((b, i) => {
          b.classList.toggle('is-active', i === pageIndex);
        });
      }
    }

    function renderPager(n) {
      if (!pager) return;
      if (n <= 1) { pager.innerHTML = ''; return; }
      const buttons = [];
      for (let i = 0; i < n; i++) {
        buttons.push(`<button type="button" class="num${i === pageIndex ? ' is-active' : ''}" data-page="${i}" aria-label="${i + 1}페이지">${i + 1}</button>`);
      }
      pager.innerHTML = buttons.join('');
      pager.querySelectorAll('.num').forEach((b) => {
        b.addEventListener('click', () => {
          pageIndex = parseInt(b.dataset.page, 10);
          apply();
        });
      });
    }

    prev && prev.addEventListener('click', () => { if (pageIndex > 0) { pageIndex--; apply(); } });
    next && next.addEventListener('click', () => { if (pageIndex < totalPages - 1) { pageIndex++; apply(); } });

    root.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft' && prev && !prev.disabled) prev.click();
      if (e.key === 'ArrowRight' && next && !next.disabled) next.click();
    });

    let raf;
    window.addEventListener('resize', () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => setTimeout(compute, 120));
    });
    compute();
  }

  document.querySelectorAll('[data-vehicle-slider]').forEach(init);
})();
