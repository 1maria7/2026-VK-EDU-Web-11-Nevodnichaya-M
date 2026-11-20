(() => {
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

    document.querySelectorAll("[data-correct-widget]").forEach((widget) => {
        const checkbox = widget.querySelector(
            "[data-correct-checkbox]"
        );
        const errorElement = widget.querySelector(
            "[data-correct-error]"
        );
        const correctUrl = widget.dataset.correctUrl;

        if (!checkbox || !errorElement) {
            return;
        }

        let savedState = checkbox.checked;

        function showError(message) {
            errorElement.textContent = message;
            errorElement.hidden = false;
        }

        checkbox.addEventListener("change", async () => {
            errorElement.textContent = "";
            errorElement.hidden = true;

            const csrfToken = getCsrfToken();

            if (!csrfToken || !correctUrl) {
                checkbox.checked = savedState;
                showError("Cannot send request. Refresh the page.");
                return;
            }

            checkbox.disabled = true;

            try {
                const response = await fetch(correctUrl, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "X-CSRFToken": csrfToken,
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                    },
                    body: new URLSearchParams({
                        question_id: widget.dataset.questionId,
                        is_correct: checkbox.checked ? "true" : "false",
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
                        message || `Request failed (HTTP ${response.status}).`
                    );
                }

                if (typeof data.is_correct !== "boolean") {
                    throw new Error("Invalid server response.");
                }

                checkbox.checked = data.is_correct;
                savedState = data.is_correct;

            } catch (error) {
                checkbox.checked = savedState;

                showError(
                    error.message || "Failed to update correct answer."
                );

            } finally {
                checkbox.disabled = false;
            }
        });
    });
})();