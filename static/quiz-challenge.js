document.addEventListener("DOMContentLoaded", () => {
	const container = document.querySelector(".quiz-challenge");
	const progressFill = document.querySelector(".qc-progress-fill");

	if (progressFill) {
		const progressValue = parseFloat(progressFill.dataset.progress || "0");
		const clamped = Math.max(0, Math.min(progressValue, 100));
		progressFill.style.width = `${clamped}%`;
	}

	if (container) {
		const questionIndex = Number.parseInt(
			container.dataset.questionIndex || "0",
			10,
		);
		const questionTotal = Number.parseInt(
			container.dataset.questionTotal || "0",
			10,
		);
		const questionMeta = container.querySelector(".qc-question-meta");

		if (questionMeta && questionIndex && questionTotal) {
			questionMeta.textContent = `Question ${questionIndex}/${questionTotal}`;
		}
	}
});
