// Home page: keep "Today" / "Yesterday" true for the visitor.
//
// The build writes the labels relative to the UTC day it ran ("Today,
// 00:39 UTC"). The daily build runs at ~06:00 UTC, so between midnight UTC and
// the next build (or longer, if a build fails) those words would be a day
// behind. This script recomputes them from the visitor's own clock, still in
// UTC: 0 days ago = "Today", 1 = "Yesterday", older = the date. The time part
// never changes. Without JavaScript the page says which day "today" means,
// so a stale label can still be read correctly.
(function () {
  "use strict";

  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var DAY_MS = 24 * 3600 * 1000;

  function utcDay(date) {   // midnight UTC of that instant's UTC day, in ms
    return Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate());
  }
  function parseDay(iso) {   // "2026-09-24" -> ms at 00:00 UTC
    var p = iso.split("-");
    return Date.UTC(+p[0], +p[1] - 1, +p[2]);
  }
  function formatDay(dayMs) {   // "24 Sep 2026", like the build
    var d = new Date(dayMs);
    return ("0" + d.getUTCDate()).slice(-2) + " " + MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear();
  }
  function label(dayMs, todayMs) {
    var diff = Math.round((todayMs - dayMs) / DAY_MS);
    if (diff === 0) return "Today";
    if (diff === 1) return "Yesterday";
    return formatDay(dayMs);
  }

  var anchor = document.querySelector("[data-today]");
  if (!anchor) return;
  var today = utcDay(new Date());
  if (today === parseDay(anchor.getAttribute("datetime"))) return;   // still the build's day

  anchor.setAttribute("datetime", new Date(today).toISOString().slice(0, 10));
  anchor.textContent = formatDay(today);
  document.querySelectorAll("time[data-relative]").forEach(function (el) {
    var text = el.textContent;
    var comma = text.indexOf(",");
    var timePart = el.hasAttribute("data-date-only") || comma < 0 ? "" : text.slice(comma);
    el.textContent = label(parseDay(el.getAttribute("data-day")), today) + timePart;
  });
})();
