// Brand logo upload — drop zone + click, preview after upload.
(function () {
  const dropzone = document.getElementById('brand-logo-dropzone');
  const input = document.getElementById('brand-logo-input');
  const current = document.getElementById('brand-logo-current');
  if (!dropzone || !input || !current) return;
  const brandId = parseInt(current.dataset.brandId, 10);

  async function upload(file) {
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await window.apiFetch(`/admin/api/brands/${brandId}/logo`, {
        method: 'POST',
        body: fd,
      });
      // Refresh the current-logo panel
      current.innerHTML =
        `<img src="${res.logo_path}?t=${Date.now()}" alt="" />` +
        `<div class="brand-logo-meta"><div class="path">${res.logo_path}</div>` +
        `<div style="color:var(--muted);font-size:12px;">새 파일을 업로드하면 대체됩니다.</div></div>`;
    } catch (e) {
      alert('업로드 실패: ' + (e.payload && e.payload.error || e.message));
    }
  }

  dropzone.addEventListener('click', () => input.click());
  input.addEventListener('change', () => upload(input.files && input.files[0]));
  dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('is-drag'); });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('is-drag'));
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('is-drag');
    upload(e.dataTransfer.files && e.dataTransfer.files[0]);
  });
})();
