// MatchPet - Login do adotante (necessário para solicitar adoção, HU05).

const form = document.getElementById("form-login");
const feedback = document.getElementById("feedback");
const btn = document.getElementById("btn-entrar");

function destino(adotanteId) {
  const voltar = new URLSearchParams(window.location.search).get("voltar");
  // Só aceita voltar para uma tela do próprio sistema (sem "/" nem endereço externo).
  if (voltar && /^[\w-]+\.html(\?[\w=&%-]*)?$/.test(voltar)) return voltar;
  return "compatibilidade.html";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  document.querySelectorAll(".erro").forEach((el) => (el.textContent = ""));
  const email = form.email.value.trim();
  const senha = form.senha.value;
  let valido = true;
  if (!email) { document.querySelector('[data-erro="email"]').textContent = "Informe o e-mail."; valido = false; }
  if (!senha) { document.querySelector('[data-erro="senha"]').textContent = "Informe a senha."; valido = false; }
  if (!valido) return;

  btn.disabled = true;
  btn.textContent = "Entrando...";
  try {
    const resposta = await fetch(`${API_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha }),
    });
    const corpo = await resposta.json().catch(() => ({}));
    if (!resposta.ok) {
      mensagemMP(feedback, resposta.status === 401 ? "E-mail ou senha incorretos." : "Não foi possível entrar. Tente novamente.", "erro");
      return;
    }
    Sessao.salvar(corpo);
    window.location.href = destino(corpo.adotante_id);
  } catch (erro) {
    mensagemMP(feedback, "Erro de conexão com o servidor. Tente novamente.", "erro");
    console.error(erro);
  } finally {
    btn.disabled = false;
    btn.textContent = "Entrar";
  }
});
