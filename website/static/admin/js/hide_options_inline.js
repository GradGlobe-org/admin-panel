document.addEventListener("DOMContentLoaded", function() {
    const selects = document.querySelectorAll('[id^="id_questions-"]'); 
    const inlines = document.querySelectorAll(".inline-group");

    function toggleInlines(select) {
        if (select.value === "subjective") {
            inlines.forEach(el => el.style.display = "none");
        } else {
            inlines.forEach(el => el.style.display = "");
        }
    }

    selects.forEach(select => {
        select.addEventListener("change", () => toggleInlines(select));
        toggleInlines(select); // run on page load for each select
    });
});
