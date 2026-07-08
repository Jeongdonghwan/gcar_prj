// Favorite toggle — attached directly to fav buttons so we can stopPropagation
// (they usually sit inside <a> cards).
(function () {
  function bind(btn) {
    if (btn._favBound) return;
    btn._favBound = true;
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const vid = btn.dataset.vehicleId;
      try {
        const res = await window.apiFetch(`/api/favorites/${vid}`, { method: 'POST' });
        btn.classList.toggle('is-active', !!res.favored);
        btn.setAttribute('aria-pressed', res.favored ? 'true' : 'false');
      } catch (err) {
        if (err.status === 401) {
          window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname);
        } else {
          alert('찜 처리 실패: ' + (err.payload && err.payload.error || err.message));
        }
      }
    });
  }
  function scan() { document.querySelectorAll('[data-fav-toggle]').forEach(bind); }
  document.addEventListener('DOMContentLoaded', scan);
  scan();
})();
