// My shelf page: the visitor's marked books and papers, plus export and import.
//
// The page contains a hidden catalogue of every published book and paper
// ([data-shelf-catalog], each item with data-id and data-kind). This script
// moves the marked ones into the "To read" and "Read" sections, books into a
// shelf of covers and papers into a list (and back when a mark is removed), so
// there is never a second copy of an item on the page.
//
// Export file format (also accepted by Import):
//   { "format": "aisafetyweb-reading", "version": 1,
//     "exported": "2026-09-23T10:00:00.000Z",
//     "items": { "sleeper-agents": { "status": "read", "updated": "..." } } }
(function () {
  "use strict";

  var site = window.AiSafetyWeb || {};
  var store = site.readingStore;
  var shelf = document.querySelector("[data-shelf]");
  var catalog = document.querySelector("[data-shelf-catalog]");
  if (!store || !shelf || !catalog) return;

  var FORMAT = "aisafetyweb-reading";
  var MAX_IMPORT_BYTES = 1024 * 1024;
  var message = shelf.querySelector("[data-io-message]");

  // Remember each item's place in the catalogue, to keep the site's order.
  var items = {};
  var order = [];
  catalog.querySelectorAll(":scope > [data-id]").forEach(function (item) {
    items[item.dataset.id] = item;
    order.push(item.dataset.id);
  });

  var STATUSES = ["to-read", "read"];
  var KINDS = ["book", "paper"];

  function list(status, kind) {
    return shelf.querySelector('[data-shelf-list="' + status + '"][data-kind="' + kind + '"]');
  }

  function render() {
    var counts = {};
    STATUSES.forEach(function (status) {
      KINDS.forEach(function (kind) { counts[status + "-" + kind] = 0; });
    });

    order.forEach(function (id) {
      var item = items[id];
      var status = store.get(id);
      var target = status ? list(status, item.dataset.kind) : null;
      if (target) counts[status + "-" + item.dataset.kind]++;
      (target || catalog).appendChild(item);  // appendChild moves the element
    });

    STATUSES.forEach(function (status) {
      var total = 0;
      KINDS.forEach(function (kind) {
        var n = counts[status + "-" + kind];
        shelf.querySelector('[data-shelf-group="' + status + "-" + kind + '"]').hidden = n === 0;
        total += n;
      });
      shelf.querySelector('[data-shelf-count="' + status + '"]').textContent = total;
      shelf.querySelector('[data-shelf-empty="' + status + '"]').hidden = total > 0;
    });

    // Marks for entries that are no longer published (removed, or not yet
    // on this site): kept in storage and in exports, but not shown.
    var orphans = Object.keys(store.all()).filter(function (id) { return !items[id]; });
    var note = shelf.querySelector("[data-shelf-orphans]");
    note.hidden = orphans.length === 0;
    note.textContent = orphans.length + " of your marks refer to entries that are not on the site " +
                       "right now. They are kept, and included when you export.";

    shelf.querySelector("[data-storage-warning]").hidden = store.persistent;
  }

  function say(text) { message.textContent = text; }

  // --- Export: download the marks as a JSON file ---------------------------
  shelf.querySelector("[data-export]").addEventListener("click", function () {
    var marks = store.all();
    var data = { format: FORMAT, version: 1, exported: new Date().toISOString(), items: marks };
    var blob = new Blob([JSON.stringify(data, null, 2) + "\n"], { type: "application/json" });
    var link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "ai-safety-web-shelf-" + data.exported.slice(0, 10) + ".json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(function () { URL.revokeObjectURL(link.href); }, 1000);
    say("Exported " + Object.keys(marks).length + " marks.");
  });

  // --- Import: read a file, check it, merge it -----------------------------
  var input = shelf.querySelector("[data-import]");
  input.addEventListener("change", function () {
    var file = input.files && input.files[0];
    input.value = "";  // so choosing the same file again fires "change"
    if (!file) return;
    if (file.size > MAX_IMPORT_BYTES) {
      say("That file is too large to be a shelf export. Nothing was imported.");
      return;
    }
    var reader = new FileReader();
    reader.onload = function () {
      var data;
      try {
        data = JSON.parse(reader.result);
      } catch (e) {
        say("That file is not valid JSON. Nothing was imported.");
        return;
      }
      if (!data || data.format !== FORMAT || !data.items || typeof data.items !== "object") {
        say("That file is not a shelf export from this site. Nothing was imported.");
        return;
      }
      var ids = Object.keys(data.items);
      var valid = {};
      ids.forEach(function (id) {
        if (site.isValidMark(id, data.items[id])) valid[id] = data.items[id];
      });
      var skipped = ids.length - Object.keys(valid).length;
      var result = store.merge(valid);
      say("Imported " + Object.keys(valid).length + " marks: " + result.added + " new, " +
          result.updated + " changed" + (skipped ? ", " + skipped + " invalid ones skipped" : "") + ".");
    };
    reader.onerror = function () { say("The file could not be read. Nothing was imported."); };
    reader.readAsText(file);
  });

  store.subscribe(render);
  shelf.hidden = false;
  render();
})();
