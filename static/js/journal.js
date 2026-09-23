// My Own Path → Journal: one month at a time.
//
// Without JavaScript every month is shown, newest first, and the bars of the
// chart are plain links to each month. This script shows the month selector
// (with Older / Newer buttons), hides every month but the chosen one, and
// keeps the choice in the URL (#journal-2026-09), so a month can be linked
// and the browser's Back button works. Default: the newest month.
(function () {
  "use strict";

  var root = document.querySelector("[data-journal]");
  if (!root) return;
  var sections = Array.prototype.slice.call(root.querySelectorAll("[data-journal-month]"));
  var controls = root.querySelector("[data-journal-controls]");
  var select = root.querySelector("[data-journal-select]");
  if (!sections.length || !controls || !select) return;

  // Newest first, as in the HTML.
  var months = sections.map(function (s) { return s.dataset.journalMonth; });
  var older = controls.querySelector('[data-journal-step="older"]');
  var newer = controls.querySelector('[data-journal-step="newer"]');
  var PREFIX = "#journal-";

  function monthFromHash() {
    var hash = window.location.hash;
    if (hash.indexOf(PREFIX) !== 0) return null;
    var month = hash.slice(PREFIX.length);
    return months.indexOf(month) >= 0 ? month : null;
  }

  function show(month) {
    sections.forEach(function (s) { s.hidden = s.dataset.journalMonth !== month; });
    select.value = month;
    var i = months.indexOf(month);
    older.disabled = i === months.length - 1;
    newer.disabled = i === 0;
    root.querySelectorAll("[data-journal-link]").forEach(function (link) {
      if (link.dataset.journalLink === month) link.setAttribute("aria-current", "true");
      else link.removeAttribute("aria-current");
    });
  }

  // Changing the month = changing the URL; the hashchange handler shows it.
  function choose(month) {
    if (window.location.hash === PREFIX + month) show(month);
    else window.location.hash = PREFIX + month;
  }

  controls.hidden = false;
  show(monthFromHash() || months[0]);

  select.addEventListener("change", function () { choose(select.value); });
  older.addEventListener("click", function () {
    var i = months.indexOf(select.value);
    if (i < months.length - 1) choose(months[i + 1]);
  });
  newer.addEventListener("click", function () {
    var i = months.indexOf(select.value);
    if (i > 0) choose(months[i - 1]);
  });
  window.addEventListener("hashchange", function () {
    var month = monthFromHash();
    if (month) show(month);
  });
})();
