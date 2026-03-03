/**
 * Theme toggle functionality for index.html
 */

// Toggle between light and dark themes
function toggleTheme() {
    var body = document.body;
    if (body.hasAttribute("data-theme")) {
        body.removeAttribute("data-theme");
        localStorage.removeItem("theme");
    } else {
        body.setAttribute("data-theme", "dark");
        localStorage.setItem("theme", "dark");
    }
}

// Load saved theme preference on page load
(function() {
    if (localStorage.getItem("theme") === "dark") {
        document.body.setAttribute("data-theme", "dark");
    }
})();
