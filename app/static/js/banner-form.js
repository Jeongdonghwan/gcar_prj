// Banner image upload — mirror of brand-form.js.
(function () {
  const dropzone = document.getElementById('banner-image-dropzone');
  const input = document.getElementById('banner-image-input');
  const current = document.getElementById('banner-image-current');
  if (!dropzone || !input || !current) return;
  const bannerId = parseInt(current.dataset.bannerId, 10);

  async function upload(file) {
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await window.apiFetch(`/admin/api/banners/${bannerId}/image`, {
        method: 'POST',
        body: fd,
      });
      current.innerHTML =
        `<img src="${res.image_path}?t=${Date.now()}" alt="" />` +
        `<div class="brand-logo-meta"><div class="path">${res.image_path}</div>` +
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
