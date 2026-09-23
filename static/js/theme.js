// Light / dark toggle in the header.
//
// Without JavaScript (or before the visitor chooses) the site follows the
// system setting through CSS (prefers-color-scheme). This script shows the
// toggle and saves the choice in localStorage under "theme". A small inline
// script in templates/base.html applies the saved choice before the page is
// painted, so there is no flash of the wrong theme.
(function () {
  "use strict";

  var button = document.querySelector("[data-theme-toggle]");
  if (!button) return;
  var root = document.documentElement;
  var systemDark = window.matchMedia("(prefers-color-scheme: dark)");

  function current() {
    return root.dataset.theme || (systemDark.matches ? "dark" : "light");
  }

  function label() {
    // The label names the action: what a click switches to.
    button.textContent = current() === "dark" ? "Light mode" : "Dark mode";
  }

  button.hidden = false;
  label();
  button.addEventListener("click", function () {
    var next = current() === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    try { localStorage.setItem("theme", next); } catch (e) { /* storage blocked: works for this page only */ }
    label();
  });
  // If the system theme changes and the visitor never chose, update the label.
  if (systemDark.addEventListener) systemDark.addEventListener("change", label);
})();
