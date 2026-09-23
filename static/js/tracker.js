// "To read" / "Read" buttons (the track_buttons macro in templates/_macros.html).
//
// The buttons are in the HTML but hidden; without JavaScript there is nowhere
// to save a mark, so they stay hidden. This script shows them, reflects the
// saved mark with aria-pressed, and saves clicks through the ReadingStore
// (static/js/reading-store.js). Clicking the active button again removes the mark.
(function () {
  "use strict";

  var store = window.AiSafetyWeb && window.AiSafetyWeb.readingStore;
  if (!store) return;

  function refresh() {
    document.querySelectorAll("[data-track]").forEach(function (group) {
      var status = store.get(group.dataset.track);
      group.hidden = false;
      group.querySelectorAll("button[data-status]").forEach(function (button) {
        button.setAttribute("aria-pressed", String(button.dataset.status === status));
      });
    });
    document.querySelectorAll("[data-track-hint]").forEach(function (hint) {
      hint.hidden = false;
    });
  }

  // One listener for the whole page, so buttons moved around later
  // (e.g. by my-shelf.js) keep working.
  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-track] button[data-status]");
    if (!button) return;
    var id = button.closest("[data-track]").dataset.track;
    var status = button.dataset.status;
    store.set(id, store.get(id) === status ? null : status);
  });

  store.subscribe(refresh);
  refresh();
})();
