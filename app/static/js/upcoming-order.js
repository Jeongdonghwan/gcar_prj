// Admin upcoming order — SortableJS with debounced PATCH autosave + toast.
(function () {
  const listA = document.getElementById('up-list-a');
  const listB = document.getElementById('up-list-b');
  if (!listA || !listB || typeof Sortable === 'undefined') return;

  const toast = document.querySelector('[data-toast]');
  let timer = null;

  function showToast(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(() => toast.classList.remove('show'), 2200);
  }

  function readIds(list) {
    return Array.from(list.querySelectorAll('[data-vehicle-id]')).map((el) =>
      parseInt(el.dataset.vehicleId, 10)
    );
  }

  function refreshPositions() {
    [listA, listB].forEach((list) => {
      Array.from(list.querySelectorAll('[data-vehicle-id]')).forEach((el, i) => {
        const pos = el.querySelector('.position');
        if (pos) pos.textContent = String(i + 1);
      });
    });
  }

  function persist() {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      try {
        await window.apiFetch('/admin/api/upcoming/order', {
          method: 'PATCH',
          body: { group_a: readIds(listA), group_b: readIds(listB) },
        });
        showToast('자동 저장됨');
      } catch (e) {
        showToast('저장 실패 — 새로고침 해주세요');
      }
    }, 300);
  }

  function makeSortable(list) {
    return Sortable.create(list, {
      group: 'upcoming',
      handle: '.handle',
      animation: 180,
      ghostClass: 'sortable-ghost',
      chosenClass: 'sortable-chosen',
      onEnd: () => {
        refreshPositions();
        persist();
      },
    });
  }

  makeSortable(listA);
  makeSortable(listB);

  // Remove buttons
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-remove-vehicle]');
    if (!btn) return;
    const row = btn.closest('[data-vehicle-id]');
    if (!row) return;
    if (!confirm('업커밍에서 제외하시겠습니까? (차량은 유지됩니다)')) return;
    row.style.opacity = '0';
    row.style.transform = 'translateX(-20px)';
    setTimeout(() => {
      row.remove();
      refreshPositions();
      persist();
    }, 200);
  });

  // Add modal
  const openBtns = document.querySelectorAll('[data-open-add]');
  const modal = document.querySelector('[data-add-modal]');
  if (modal) {
    const close = () => modal.classList.remove('show');
    openBtns.forEach((b) => b.addEventListener('click', () => {
      modal.dataset.targetGroup = b.dataset.group;
      modal.classList.add('show');
    }));
    modal.addEventListener('click', (e) => { if (e.target === modal) close(); });
    modal.querySelectorAll('[data-add-candidate]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const vid = parseInt(btn.dataset.vehicleId, 10);
        const group = modal.dataset.targetGroup || 'a';
        try {
          await window.apiFetch('/admin/api/upcoming/add', {
            method: 'POST',
            body: { vehicle_id: vid, group: group },
          });
          showToast('차량이 업커밍에 추가되었습니다 — 새로고침');
          setTimeout(() => location.reload(), 600);
        } catch (e) {
          showToast('추가 실패');
        }
      });
    });

    const search = modal.querySelector('[data-add-search]');
    if (search) {
      search.addEventListener('input', () => {
        const q = (search.value || '').toLowerCase();
        modal.querySelectorAll('.candidate').forEach((row) => {
          const name = (row.dataset.name || '').toLowerCase();
          row.style.display = name.includes(q) ? '' : 'none';
        });
      });
    }
  }
})();
