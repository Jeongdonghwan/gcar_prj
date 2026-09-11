// CSRF-aware fetch helper. JSON requests pick up the meta token automatically.
(function () {
  const meta = document.querySelector('meta[name="csrf-token"]');
  const csrfToken = meta ? meta.getAttribute('content') : '';

  window.apiFetch = async function (url, options = {}) {
    const opts = Object.assign({ method: 'GET', headers: {}, credentials: 'same-origin' }, options);
    opts.headers = Object.assign({}, opts.headers);
    const method = (opts.method || 'GET').toUpperCase();
    if (method !== 'GET' && method !== 'HEAD') {
      opts.headers['X-CSRFToken'] = csrfToken;
    }
    if (opts.body && !(opts.body instanceof FormData) && typeof opts.body !== 'string') {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(opts.body);
    }
    const res = await fetch(url, opts);
    if (!res.ok) {
      const err = new Error('Request failed: ' + res.status);
      err.status = res.status;
      try { err.payload = await res.json(); } catch (e) { /* ignore */ }
      throw err;
    }
    if (res.status === 204) return null;
    const ctype = res.headers.get('Content-Type') || '';
    return ctype.includes('application/json') ? res.json() : res.text();
  };

  // Header scroll border
  const header = document.querySelector('.site-header');
  if (header) {
    const onScroll = () => header.classList.toggle('is-scrolled', window.scrollY > 8);
    document.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // Contact CTA (tel: links) — log the inquiry, then let the call proceed
  document.querySelectorAll('[data-contact-cta]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const source = btn.dataset.source || 'unknown';
      const vehicleId = btn.dataset.vehicleId || null;
      // fire-and-forget: tel: navigation must not wait on the request
      window.apiFetch('/api/inquiries', {
        method: 'POST',
        body: { source: source, vehicle_id: vehicleId },
      }).catch(() => { /* swallow */ });
    });
  });
})();
