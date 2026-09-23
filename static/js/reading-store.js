// ReadingStore: where a visitor's "To read" / "Read" marks are kept.
//
// Every page talks to the store only through this interface, so a
// server-backed store (with accounts) could replace it later without touching
// the pages:
//
//   store.get(id)          -> "to-read" | "read" | null
//   store.set(id, status)  status "to-read" | "read", or null to remove the mark
//   store.all()            -> { id: { status, updated } }  (a copy)
//   store.merge(items)     add/overwrite marks from an import -> { added, updated }
//   store.subscribe(fn)    fn() runs after every change (also from other tabs)
//   store.persistent       false if marks can't be saved (they last until the page closes)
//
// Marks are keyed by the entry's `id` from data/papers.yaml or data/books.yaml,
// the same id everywhere on the site.
//
// This implementation uses localStorage: private to this browser, never sent
// anywhere. Every access is wrapped in try/catch, because localStorage can be
// missing or blocked (private windows, strict privacy settings, full storage).
(function () {
  "use strict";

  var KEY = "aisafetyweb.reading.v1";
  var STATUSES = ["to-read", "read"];
  var ID_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

  function isValidMark(id, mark) {
    return ID_RE.test(id) && mark && typeof mark === "object" &&
           STATUSES.indexOf(mark.status) !== -1;
  }

  function LocalReadingStore() {
    this.listeners = [];
    this.items = {};
    this.persistent = true;
    try {
      var probe = KEY + ".probe";
      window.localStorage.setItem(probe, "1");
      window.localStorage.removeItem(probe);
    } catch (e) {
      this.persistent = false;  // fall back to memory for this page only
    }
    this.load();

    var self = this;
    // Another tab changed the marks: reload and redraw.
    window.addEventListener("storage", function (event) {
      if (event.key === KEY) { self.load(); self.notify(); }
    });
  }

  LocalReadingStore.prototype.load = function () {
    if (!this.persistent) return;
    var parsed = null;
    try {
      parsed = JSON.parse(window.localStorage.getItem(KEY) || "null");
    } catch (e) {
      parsed = null;  // unreadable or corrupt: start empty rather than crash
    }
    var items = {};
    if (parsed && parsed.items && typeof parsed.items === "object") {
      Object.keys(parsed.items).forEach(function (id) {
        if (isValidMark(id, parsed.items[id])) {
          items[id] = { status: parsed.items[id].status, updated: String(parsed.items[id].updated || "") };
        }
      });
    }
    this.items = items;
  };

  LocalReadingStore.prototype.save = function () {
    if (!this.persistent) return;
    try {
      window.localStorage.setItem(KEY, JSON.stringify({ version: 1, items: this.items }));
    } catch (e) {
      this.persistent = false;  // e.g. storage full; keep working in memory
    }
  };

  LocalReadingStore.prototype.notify = function () {
    this.listeners.forEach(function (fn) { fn(); });
  };

  LocalReadingStore.prototype.get = function (id) {
    return this.items[id] ? this.items[id].status : null;
  };

  LocalReadingStore.prototype.set = function (id, status) {
    if (status === null) {
      delete this.items[id];
    } else if (STATUSES.indexOf(status) !== -1 && ID_RE.test(id)) {
      this.items[id] = { status: status, updated: new Date().toISOString() };
    } else {
      return;
    }
    this.save();
    this.notify();
  };

  LocalReadingStore.prototype.all = function () {
    return JSON.parse(JSON.stringify(this.items));
  };

  LocalReadingStore.prototype.merge = function (items) {
    var result = { added: 0, updated: 0 };
    var self = this;
    Object.keys(items).forEach(function (id) {
      if (!isValidMark(id, items[id])) return;
      if (self.items[id]) {
        if (self.items[id].status !== items[id].status) result.updated++;
      } else {
        result.added++;
      }
      self.items[id] = { status: items[id].status,
                         updated: String(items[id].updated || new Date().toISOString()) };
    });
    this.save();
    this.notify();
    return result;
  };

  LocalReadingStore.prototype.subscribe = function (fn) {
    this.listeners.push(fn);
  };

  window.AiSafetyWeb = window.AiSafetyWeb || {};
  window.AiSafetyWeb.isValidMark = isValidMark;
  window.AiSafetyWeb.readingStore = new LocalReadingStore();
})();
