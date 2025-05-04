const tabs = document.querySelectorAll(".tab");
const editors = document.querySelectorAll(".code-editor");
const htmlCode = document.getElementById("html-code");
const cssCode = document.getElementById("css-code");
const jsCode = document.getElementById("js-code");

tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        tabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");

        editors.forEach((editor) => editor.classList.remove("active"));
        document
        .getElementById(tab.dataset.lang + "-editor")
        .classList.add("active");
    });
});

function updateLineNumbers(textarea, linesDiv) {
    const lines = textarea.value.split("\n").length;
    linesDiv.innerText = Array.from(
        { length: lines },
        (_, i) => i + 1
    ).join("\n");
}

function syncScroll(textarea, linesDiv) {
    textarea.addEventListener("scroll", () => {
        linesDiv.scrollTop = textarea.scrollTop;
    });
}
function isHTMLValid(html) {
    const doc = new DOMParser().parseFromString(html, "text/html");
    return !doc.querySelector("parsererror");
}

function updateOutput() {
    const html = htmlCode.value;
    const css = `<style>${cssCode.value}</style>`;
    const js = `<script>${jsCode.value}<\/script>`;
    const finalCode = `<!DOCTYPE html><html><head>${css}</head><body>${html}${js}</body></html>`;

    if (isHTMLValid(finalCode)) {
        document.getElementById("output-frame").srcdoc = finalCode;
    } else {
        console.error("Invalid HTML!");
    }
}

[htmlCode, cssCode, jsCode].forEach((textarea) => {
const linesDiv = document.getElementById(
    textarea.id.replace("-code", "-lines")
);

textarea.addEventListener("input", () => {
    updateLineNumbers(textarea, linesDiv);
    updateOutput();
});

syncScroll(textarea, linesDiv);
updateLineNumbers(textarea, linesDiv);
});

updateOutput(); // initial