// Auth page — consent box master toggle.
(function () {
  const master = document.getElementById('consent-all');
  const children = document.querySelectorAll('[data-consent-child]');
  if (!master || !children.length) return;
  master.addEventListener('change', () => {
    children.forEach((c) => { c.checked = master.checked; });
  });
  children.forEach((c) => c.addEventListener('change', () => {
    master.checked = Array.from(children).every((x) => x.checked);
  }));
})();
