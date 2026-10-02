const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const sendButton = document.querySelector("#send-button");
const sessionValue = document.querySelector("#session-value");
const traceValue = document.querySelector("#trace-value");
const modelValue = document.querySelector("#model-value");
const requestStatus = document.querySelector("#request-status");
const sourcesList = document.querySelector("#sources");

let sessionId = createSessionId();
sessionValue.textContent = sessionId;

function createSessionId() {
  return `demo-${crypto.randomUUID()}`;
}

function addMessage(role, text, extraClass = "") {
  const article = document.createElement("article");
  article.className = `message ${role === "Usuario" ? "user-message" : "agent-message"} ${extraClass}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = role === "Usuario" ? "U" : "A";

  const content = document.createElement("div");
  content.className = "message-content";
  const author = document.createElement("span");
  author.className = "message-author";
  author.textContent = role;
  const paragraph = document.createElement("p");
  paragraph.textContent = text;

  content.append(author, paragraph);
  article.append(avatar, content);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

function updateSources(sources) {
  sourcesList.replaceChildren();
  const values = sources.length ? sources : ["No reportadas en esta respuesta"];
  for (const source of values) {
    const item = document.createElement("li");
    item.textContent = source;
    sourcesList.append(item);
  }
}

async function sendMessage(message) {
  addMessage("Usuario", message);
  const pending = addMessage("Agente", "Consultando fuentes y validando la información…", "typing");
  sendButton.disabled = true;
  requestStatus.textContent = "Procesando";

  try {
    const response = await fetch("/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, user_id: "demo-user", message }),
    });
    const payload = await response.json();
    pending.remove();

    if (!response.ok) {
      const detail = payload.detail || {};
      throw new Error(detail.message || "La consulta no pudo completarse");
    }

    addMessage("Agente", payload.answer);
    traceValue.textContent = payload.trace_id;
    modelValue.textContent = payload.model_id;
    requestStatus.textContent = "Completado";
    updateSources(payload.sources);
  } catch (error) {
    pending.remove();
    addMessage("Agente", `No fue posible completar la consulta. ${error.message}`);
    requestStatus.textContent = "Error";
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message || sendButton.disabled) return;
  input.value = "";
  sendMessage(message);
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt;
    input.focus();
  });
});

document.querySelector("#new-session").addEventListener("click", () => {
  sessionId = createSessionId();
  sessionValue.textContent = sessionId;
  traceValue.textContent = "Aún sin ejecución";
  requestStatus.textContent = "Listo";
  updateSources([]);
  messages.replaceChildren();
  addMessage("Agente", "Nueva sesión iniciada. Indica el cliente que deseas consultar.");
  input.focus();
});
