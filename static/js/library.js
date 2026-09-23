// The Library: book covers, reading marks on the shelf, and the book card dialog.
//
// Progressive enhancement. Without JavaScript every book is a link to its own
// page (library/<id>/), which shows the full card. With JavaScript:
//   - a cover image that fails to load is removed, so the typographic cover
//     underneath shows instead;
//   - each book on a shelf shows a small "To read" / "Read" mark;
//   - clicking a book opens its card in the native <dialog> instead of
//     leaving the page. showModal() moves focus into the dialog and makes the
//     rest of the page inert; Esc, the × button or a click on the backdrop
//     close it, and focus goes back to the book that opened it.
// The card comes from a <template data-card="<id>"> rendered by the build.
(function () {
  "use strict";

  var site = window.AiSafetyWeb || {};
  var store = site.readingStore;
  var LABELS = { "to-read": "To read", "read": "Read" };

  // --- Covers: fall back to the typographic cover ------------------------------
  function watchCovers(root) {
    root.querySelectorAll("img[data-cover]").forEach(function (img) {
      function drop() { img.remove(); }
      if (img.complete && img.naturalWidth === 0) drop();
      else img.addEventListener("error", drop);
    });
  }
  watchCovers(document);

  // --- Reading marks on the shelf ---------------------------------------------
  function refreshMarks() {
    if (!store) return;
    document.querySelectorAll("[data-book-mark]").forEach(function (mark) {
      var status = store.get(mark.dataset.bookMark);
      mark.hidden = !status;
      mark.textContent = status ? LABELS[status] : "";
      mark.className = "book-mark" + (status ? " book-mark-" + status : "");
    });
  }
  if (store) store.subscribe(refreshMarks);
  refreshMarks();

  // --- The book card dialog ---------------------------------------------------
  var dialog = document.querySelector("[data-book-dialog]");
  if (!dialog || typeof dialog.showModal !== "function") return;  // old browser: links still work
  var body = dialog.querySelector("[data-book-dialog-body]");
  var opener = null;

  document.addEventListener("click", function (event) {
    // Ctrl/Cmd/Shift-click keeps the normal link behaviour (open in a new tab).
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    var link = event.target.closest("a[data-book]");
    if (!link) return;
    var template = document.querySelector('template[data-card="' + link.dataset.book + '"]');
    if (!template) return;  // no card on this page: follow the link
    event.preventDefault();

    body.replaceChildren(template.content.cloneNode(true));
    var title = body.querySelector(".book-card-title");
    if (title) {
      dialog.removeAttribute("aria-label");
      dialog.setAttribute("aria-labelledby", title.id);
    }
    watchCovers(body);
    if (site.refreshTracker) site.refreshTracker();  // show the To read / Read buttons
    opener = link;
    dialog.showModal();
  });

  // A click on the backdrop (outside the card) lands on the <dialog> itself.
  dialog.addEventListener("click", function (event) {
    if (event.target === dialog) dialog.close();
  });

  dialog.addEventListener("close", function () {
    // The "close" event arrives a moment after the dialog closes. If a book
    // was opened again in the meantime, don't empty its new card.
    if (dialog.open) return;
    body.replaceChildren();
    if (opener) opener.focus();
    opener = null;
  });
})();
