function getCsrfToken() {
    const csrfInput = document.querySelector(
        'input[name="csrfmiddlewaretoken"]'
    );

    if (csrfInput) {
        return csrfInput.value;
    }

    const cookie = document.cookie
        .split("; ")
        .find((item) => item.startsWith("csrftoken="));

    return cookie
        ? decodeURIComponent(cookie.split("=")[1])
        : null;
}


document.querySelectorAll("[data-vote-widget]").forEach((widget) => {
    const countElement = widget.querySelector(".vote-count");
    const buttons = widget.querySelectorAll(".vote-button");
    const voteUrl = widget.dataset.voteUrl;

    let isSubmitting = false;
    let hasVoted = false;

    const errorElement = document.createElement("div");
    errorElement.className = "small text-danger text-center";
    errorElement.setAttribute("role", "alert");
    errorElement.hidden = true;

    widget.appendChild(errorElement);

    function showError(message) {
        errorElement.textContent = message;
        errorElement.hidden = false;
    }

    buttons.forEach((button) => {
        button.addEventListener("click", async () => {
            if (button.disabled || isSubmitting || hasVoted) {
                return;
            }

            errorElement.hidden = true;
            errorElement.textContent = "";

            const csrfToken = getCsrfToken();

            if (!csrfToken) {
                showError("CSRF token not found. Refresh the page.");
                return;
            }

            if (!voteUrl) {
                showError("Voting URL not found.");
                return;
            }

            const value = button.dataset.vote === "up" ? 1 : -1;

            isSubmitting = true;

            buttons.forEach((item) => {
                item.disabled = true;
            });

            try {
                const response = await fetch(voteUrl, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "X-CSRFToken": csrfToken,
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                    },
                    body: new URLSearchParams({
                        value: String(value),
                    }),
                });

                const data = await response.json().catch(() => ({}));

                if (!response.ok) {
                    let message = data.error;

                    if (!message && data.errors) {
                        message = Object.values(data.errors)
                            .flat()
                            .map((error) => error.message)
                            .join(" ");
                    }

                    throw new Error(
                        message || `Voting failed (HTTP ${response.status}).`
                    );
                }

                if (typeof data.rating !== "number") {
                    throw new Error("Invalid server response.");
                }

                countElement.textContent = data.rating;
                widget.dataset.count = String(data.rating);

                hasVoted = true;

                button.classList.add("active");
                button.setAttribute("aria-pressed", "true");

                buttons.forEach((item) => {
                    item.disabled = true;
                    item.title = "You have already voted";
                });

            } catch (error) {
                showError(error.message || "Voting failed.");

            } finally {
                isSubmitting = false;

                if (!hasVoted) {
                    buttons.forEach((item) => {
                        item.disabled = false;
                    });
                }
            }
        });
    });
});
