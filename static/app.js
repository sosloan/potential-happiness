const sampleInput = `{
  "users": [
    { "name": "Ada", "city": "London", "active": true },
    { "name": "Linus", "city": "Helsinki", "active": false },
    { "name": "Grace", "city": "New York", "active": true }
  ]
}`;

const queryField = document.querySelector("#query");
const inputField = document.querySelector("#input");
const outputField = document.querySelector("#output");
const runButton = document.querySelector("#run-button");
const copyButton = document.querySelector("#copy-button");
const resultStatus = document.querySelector("#result-status");

async function runQuery() {
  runButton.disabled = true;
  runButton.querySelector("span").textContent = "Running…";
  outputField.className = "output empty";
  outputField.textContent = "Running jq…";
  resultStatus.className = "result-status";
  resultStatus.textContent = "Working";
  copyButton.disabled = true;

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: queryField.value, input: inputField.value }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not run the query.");

    outputField.textContent = result.output || "(no output)";
    outputField.className = result.ok ? "output" : "output error";
    resultStatus.textContent = result.ok ? "Query completed" : "Query error";
    resultStatus.className = result.ok ? "result-status" : "result-status error";
    copyButton.disabled = !result.ok || !result.output;
  } catch (error) {
    outputField.textContent = error.message || "Unable to connect to the local jq server.";
    outputField.className = "output error";
    resultStatus.textContent = "Could not run query";
    resultStatus.className = "result-status error";
  } finally {
    runButton.disabled = false;
    runButton.querySelector("span").textContent = "Run query";
  }
}

runButton.addEventListener("click", runQuery);
document.querySelector("#sample-button").addEventListener("click", () => {
  inputField.value = sampleInput;
  queryField.value = ".users[] | {name, city}";
  queryField.focus();
});
copyButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(outputField.textContent);
    copyButton.textContent = "Copied!";
    window.setTimeout(() => { copyButton.textContent = "Copy"; }, 1200);
  } catch {
    copyButton.textContent = "Copy unavailable";
  }
});
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") runQuery();
});
