// Filter menus for lists of items (news entries, papers).
//
// Progressive enhancement: the HTML already contains every item, so the page
// works without JavaScript. This script only shows the filter menus and hides
// items that don't match.
//
// How it reads the page (see templates/_macros.html):
//   [data-filter-root]         one filterable list
//   [data-filters]             its <form> of menus (starts hidden)
//   <select data-filter="X">   a menu; empty value = no filter
//   [data-filter-item]         an item; it matches menu X if the chosen value is
//                              one of the space-separated words in its data-X
//   [data-filter-group]        optional group (a day); hidden when it has no visible item
//   [data-filter-count]        "12 of 134 shown"
//   [data-filter-empty]        message shown when nothing matches
(function () {
  "use strict";

  document.querySelectorAll("[data-filter-root]").forEach(function (root) {
    var form = root.querySelector("[data-filters]");
    if (!form) return;
    var selects = form.querySelectorAll("select[data-filter]");
    var counter = form.querySelector("[data-filter-count]");
    var empty = root.querySelector("[data-filter-empty]");
    var items = root.querySelectorAll("[data-filter-item]");

    function matches(item) {
      for (var i = 0; i < selects.length; i++) {
        var wanted = selects[i].value;
        if (!wanted) continue;
        var words = (item.getAttribute("data-" + selects[i].dataset.filter) || "").split(" ");
        if (words.indexOf(wanted) === -1) return false;
      }
      return true;
    }

    function apply() {
      var shown = 0;
      items.forEach(function (item) {
        var match = matches(item);
        item.hidden = !match;
        if (match) shown++;
      });

      root.querySelectorAll("[data-filter-group]").forEach(function (group) {
        group.hidden = !group.querySelector("[data-filter-item]:not([hidden])");
      });

      if (counter) counter.textContent = shown + " of " + items.length + " shown";
      if (empty) empty.hidden = shown !== 0 || items.length === 0;
    }

    form.addEventListener("change", apply);
    form.addEventListener("submit", function (event) { event.preventDefault(); });
    form.hidden = false;
    apply();
  });
})();
