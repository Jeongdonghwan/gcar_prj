// Admin vehicle edit page — image upload, drag-reorder, set primary, delete.
(function () {
  const grid = document.getElementById('image-thumb-grid');
  const drop = document.getElementById('image-dropzone');
  const fileInput = document.getElementById('image-file-input');
  if (!grid || !drop) return;
  const vehicleId = parseInt(grid.dataset.vehicleId, 10);

  function renderCell(img) {
    const cell = document.createElement('div');
    cell.className = 'thumb-cell';
    cell.dataset.imageId = img.id;
    cell.innerHTML = `
      <img src="${img.path}" alt="">
      <span class="order">${img.sort_order + 1}</span>
      ${img.is_primary ? '<span class="primary-badge">대표</span>' : ''}
      ${!img.is_primary ? '<button type="button" class="set-primary" data-set-primary>대표 지정</button>' : ''}
      <button type="button" class="remove" data-remove-img>×</button>
    `;
    return cell;
  }

  async function uploadFiles(files) {
    if (!files.length) return;
    const fd = new FormData();
    for (const f of files) fd.append('file', f);
    try {
      const res = await window.apiFetch(`/admin/api/vehicles/${vehicleId}/images`, {
        method: 'POST',
        body: fd,
      });
      (res.images || []).forEach((img) => grid.appendChild(renderCell(img)));
    } catch (e) {
      alert('업로드 실패: ' + (e.payload && e.payload.error || e.message));
    }
  }

  drop.addEventListener('click', () => fileInput && fileInput.click());
  fileInput && fileInput.addEventListener('change', () => uploadFiles(Array.from(fileInput.files || [])));
  drop.addEventListener('dragover', (e) => { e.preventDefault(); drop.classList.add('is-drag'); });
  drop.addEventListener('dragleave', () => drop.classList.remove('is-drag'));
  drop.addEventListener('drop', (e) => {
    e.preventDefault();
    drop.classList.remove('is-drag');
    uploadFiles(Array.from(e.dataTransfer.files || []));
  });

  grid.addEventListener('click', async (e) => {
    const cell = e.target.closest('.thumb-cell');
    if (!cell) return;
    const id = parseInt(cell.dataset.imageId, 10);
    if (e.target.matches('[data-remove-img]')) {
      if (!confirm('이미지를 삭제하시겠습니까?')) return;
      try {
        await window.apiFetch(`/admin/api/vehicles/${vehicleId}/images/${id}`, { method: 'DELETE' });
        cell.remove();
      } catch (_) { alert('삭제 실패'); }
    } else if (e.target.matches('[data-set-primary]')) {
      try {
        await window.apiFetch(`/admin/api/vehicles/${vehicleId}/images/${id}/primary`, { method: 'POST' });
        location.reload();
      } catch (_) { alert('실패'); }
    }
  });

  if (typeof Sortable !== 'undefined') {
    Sortable.create(grid, {
      animation: 180,
      onEnd: async () => {
        const ids = Array.from(grid.querySelectorAll('.thumb-cell')).map((c) => parseInt(c.dataset.imageId, 10));
        try {
          await window.apiFetch(`/admin/api/vehicles/${vehicleId}/images/order`, {
            method: 'PATCH',
            body: { ids: ids },
          });
        } catch (_) { /* ignore */ }
      },
    });
  }
})();
