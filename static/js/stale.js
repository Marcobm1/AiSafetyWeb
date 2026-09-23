// "This site may be out of date" warning (templates/base.html).
//
// The page says when the news was last fetched (data-stale-since, from
// data/status.json). If that is more than data-stale-hours ago by the
// visitor's own clock, the warning is shown. The check runs in the browser on
// purpose: if the daily GitHub Actions run stops, nothing rebuilds the site,
// so a check done at build time would never fire.
(function () {
  "use strict";

  var note = document.querySelector("[data-stale-since]");
  if (!note) return;
  var since = Date.parse(note.dataset.staleSince);
  var hours = Number(note.dataset.staleHours) || 48;
  if (!isNaN(since) && Date.now() - since > hours * 3600 * 1000) note.hidden = false;
})();
