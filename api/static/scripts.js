document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("scrollToTopBtn").addEventListener("click", function() {
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    });
});