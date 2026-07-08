// Anchor-tabs on vehicle detail: highlight the tab of the section currently in view.
(function () {
  const nav = document.querySelector('.anchor-tabs');
  if (!nav) return;
  const tabs = Array.from(nav.querySelectorAll('a[href^="#"]'));
  if (!tabs.length) return;
  const sections = tabs
    .map((a) => document.querySelector(a.getAttribute('href')))
    .filter(Boolean);

  function setActive(id) {
    tabs.forEach((t) => t.classList.toggle('is-active', t.getAttribute('href') === '#' + id));
  }

  tabs.forEach((a) => {
    a.addEventListener('click', () => {
      setActive(a.getAttribute('href').substring(1));
    });
  });

  if ('IntersectionObserver' in window && sections.length) {
    const observer = new IntersectionObserver(
      (entries) => {
        // Prefer the section whose top is closest to the trigger zone
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible.length) setActive(visible[0].target.id);
      },
      { rootMargin: '-40% 0px -55% 0px', threshold: 0 }
    );
    sections.forEach((s) => observer.observe(s));
  }
})();
