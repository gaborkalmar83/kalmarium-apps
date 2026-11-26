/* Click-to-load video facade. Without JS the poster is a plain link to the MP4.
   Nothing is fetched until the visitor clicks, and nothing is stored. */
(function () {
  var links = document.querySelectorAll("a.vid[data-video]");
  Array.prototype.forEach.call(links, function (a) {
    a.addEventListener("click", function (e) {
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.button) return;
      e.preventDefault();
      var img = a.querySelector("img");
      var v = document.createElement("video");
      v.controls = true;
      v.playsInline = true;
      v.preload = "none";
      v.src = a.getAttribute("href");
      if (img) {
        v.poster = img.currentSrc || img.src;
        v.width = img.width;
        v.height = img.height;
      }
      v.className = a.className.replace(/\bvid\b/, "").trim();
      v.setAttribute("aria-label", a.getAttribute("data-video"));
      a.replaceWith(v);
      v.focus();
      var p = v.play();
      if (p && p.catch) p.catch(function () {});
    });
  });
})();
