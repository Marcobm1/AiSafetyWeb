// Source and topic filters for lists of news entries.
//
// Progressive enhancement: the HTML already contains every entry, so the page
// works without JavaScript. This script only shows the filter menus and hides
// entries that don't match. It reads the data-* attributes written by the
// `entry` and `filters` macros in templates/_macros.html.
(function () {
  "use strict";

  document.querySelectorAll("[data-filter-root]").forEach(function (root) {
    var form = root.querySelector("[data-filters]");
    if (!form) return;
    var sourceSelect = form.querySelector('[data-filter="source"]');
    var topicSelect = form.querySelector('[data-filter="topic"]');
    var counter = form.querySelector("[data-filter-count]");
    var empty = root.querySelector("[data-filter-empty]");
    var entries = root.querySelectorAll(".entry");

    function apply() {
      var source = sourceSelect.value;
      var topic = topicSelect.value;
      var shown = 0;

      entries.forEach(function (entry) {
        var topics = (entry.dataset.topics || "").split(" ");
        var match = (!source || entry.dataset.source === source) &&
                    (!topic || topics.indexOf(topic) !== -1);
        entry.hidden = !match;
        if (match) shown++;
      });

      // Hide a whole day when none of its entries is visible.
      root.querySelectorAll("[data-filter-group]").forEach(function (group) {
        group.hidden = !group.querySelector(".entry:not([hidden])");
      });

      if (counter) counter.textContent = shown + " of " + entries.length + " shown";
      if (empty) empty.hidden = shown !== 0;
    }

    form.addEventListener("change", apply);
    form.addEventListener("submit", function (event) { event.preventDefault(); });
    form.hidden = false;
    apply();
  });
})();
