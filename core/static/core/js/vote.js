
document.querySelectorAll("[data-vote-widget]").forEach((widget) => {
    const countElement = widget.querySelector(".vote-count");
    const buttons = widget.querySelectorAll(".vote-button");

    const initialCount = Number(widget.dataset.count);
    let count = initialCount;
    let selectedVote = null;

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            const vote = button.dataset.vote;

            if (selectedVote === vote) {
                selectedVote = null;
            } else {
                selectedVote = vote;
            }

            count = initialCount;

            if (selectedVote === "up") {
                count++;
            } else if (selectedVote === "down") {
                count--;
            }

            countElement.textContent = count;

            buttons.forEach((item) => {
                const isActive = item.dataset.vote === selectedVote;

                item.setAttribute("aria-pressed", String(isActive));
                item.classList.toggle("active", isActive);
            });
        });
    });
});
