// Shared across index.html (연금저축) and irp/index.html (IRP) —
// best-fee badge, sort, compare bar/modal, and modal keyboard handling
// that behave identically on both pages. Loaded via a path relative
// to each page so it resolves wherever that page itself is served from.

(function () {
  var list = document.getElementById('plans-list');
  if (!list) return;
  var entries = Array.prototype.slice.call(list.children);
  var lowest = entries.reduce(function (min, el) {
    return parseFloat(el.dataset.fee) < parseFloat(min.dataset.fee) ? el : min;
  }, entries[0]);
  if (lowest) {
    var badge = document.createElement('span');
    badge.className = 'best-fee-badge';
    badge.textContent = '최저수수료';
    lowest.querySelector('.type-tag').insertAdjacentElement('afterend', badge);
  }
})();

(function () {
  var list = document.getElementById('plans-list');
  var buttons = document.querySelectorAll('.sort-btn');
  if (!list || !buttons.length) return;
  var defaultOrder = Array.prototype.slice.call(list.children);

  function sortBy(mode) {
    var items;
    if (mode === 'fee') {
      items = Array.prototype.slice.call(list.children).sort(function (a, b) {
        return parseFloat(a.dataset.fee) - parseFloat(b.dataset.fee);
      });
    } else if (mode === 'name') {
      items = Array.prototype.slice.call(list.children).sort(function (a, b) {
        return a.dataset.name.localeCompare(b.dataset.name, 'ko');
      });
    } else {
      items = defaultOrder;
    }
    list.classList.add('resorting');
    setTimeout(function () {
      items.forEach(function (el) { list.appendChild(el); });
      list.classList.remove('resorting');
    }, 180);
  }

  buttons.forEach(function (btn) {
    btn.setAttribute('aria-pressed', btn.classList.contains('active') ? 'true' : 'false');
    btn.addEventListener('click', function () {
      buttons.forEach(function (b) { b.classList.remove('active'); b.setAttribute('aria-pressed', 'false'); });
      btn.classList.add('active');
      btn.setAttribute('aria-pressed', 'true');
      sortBy(btn.dataset.sort);
    });
  });
})();

document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') { closeCompareModal(); }
});

var compareSet = new Set();

function toggleCompare(cb) {
  var card = cb.closest('.ledger-entry');
  var name = card.dataset.name;
  if (cb.checked) { compareSet.add(name); } else { compareSet.delete(name); }
  var bar = document.getElementById('compareBar');
  document.getElementById('compareCount').textContent = compareSet.size;
  bar.style.display = compareSet.size >= 2 ? 'flex' : 'none';
}

function clearCompare() {
  compareSet.clear();
  document.querySelectorAll('.compare-cb').forEach(function (cb) { cb.checked = false; });
  document.getElementById('compareBar').style.display = 'none';
  closeCompareModal();
}

function openCompareModal() {
  var cards = Array.prototype.slice.call(document.querySelectorAll('.ledger-entry')).filter(function (c) {
    return compareSet.has(c.dataset.name);
  });
  if (!cards.length) return;

  var rows = [
    { label: '유형', get: function (c) { return c.querySelector('.type-tag').textContent; } }
  ];
  if (cards[0].dataset.match) {
    rows.push({ label: 'AI 매칭', get: function (c) { return c.dataset.match ? c.dataset.match + '%' : '-'; } });
  }
  var gridItemCount = cards[0].querySelectorAll('.ledger-item').length;
  for (var i = 0; i < gridItemCount; i++) {
    (function (idx) {
      var label = cards[0].querySelectorAll('.ledger-item')[idx].querySelector('.k').textContent;
      rows.push({ label: label, get: function (c) {
        var items = c.querySelectorAll('.ledger-item');
        return items[idx] ? items[idx].querySelector('.v').textContent : '-';
      }});
    })(i);
  }
  rows.push({ label: '수수료', get: function (c) {
    return c.querySelector('.fee .k').textContent + ' ' + c.querySelector('.fee .v').textContent;
  }});

  var html = '<table class="compare-table"><thead><tr><th></th>';
  cards.forEach(function (c) { html += '<th>' + c.dataset.name + '</th>'; });
  html += '</tr></thead><tbody>';
  rows.forEach(function (row) {
    html += '<tr><td class="k-col">' + row.label + '</td>';
    cards.forEach(function (c) { html += '<td>' + row.get(c) + '</td>'; });
    html += '</tr>';
  });
  html += '</tbody></table>';
  document.getElementById('compareTableWrap').innerHTML = html;
  document.getElementById('compareModal').style.display = 'flex';
}

function closeCompareModal() {
  document.getElementById('compareModal').style.display = 'none';
}
