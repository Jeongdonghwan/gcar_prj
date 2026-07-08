// FAQ accordion + category chip filter.
(function () {
  document.querySelectorAll('[data-faq]').forEach((item) => {
    const q = item.querySelector('.q');
    const a = item.querySelector('.a');
    if (!q || !a) return;
    q.addEventListener('click', () => {
      const open = item.classList.toggle('is-open');
      a.style.maxHeight = open ? a.scrollHeight + 'px' : '0px';
    });
  });

  document.querySelectorAll('[data-faq-cat]').forEach((chip) => {
    chip.addEventListener('click', () => {
      const cat = chip.dataset.faqCat;
      document.querySelectorAll('[data-faq-cat]').forEach((c) => c.classList.toggle('is-active', c === chip));
      document.querySelectorAll('[data-faq]').forEach((item) => {
        const match = cat === 'all' || item.dataset.category === cat;
        item.style.display = match ? '' : 'none';
        if (!match) {
          item.classList.remove('is-open');
          const a = item.querySelector('.a');
          if (a) a.style.maxHeight = '0px';
        }
      });
    });
  });
})();
