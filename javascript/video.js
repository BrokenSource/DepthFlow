// This script pauses videos outside of the viewport
// Fixme: Mkdocs Instant loading
(function() {
    function handleVideos() {
        var videos = document.getElementsByTagName("video");

        var observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.play();
                } else {
                    entry.target.pause();
                }
            });
        }, {threshold: 0.1});

        Array.from(videos).forEach(function(video) {
            video.setAttribute("playsinline", "");
            video.setAttribute("muted", "");
            video.setAttribute("loop", "");
            observer.observe(video);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", handleVideos);
    } else {
        handleVideos();
    }
})();
