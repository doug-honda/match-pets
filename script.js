// MatchPet - Cadastro do Adotante
// Integração da interface com a API (FastAPI)

const API_URL = "http://localhost:8000";

const form = document.getElementById("form-adotante");
const feedback = document.getElementById("feedback");
const btnEnviar = document.getElementById("btn-enviar");

function limparErros() {
  document.querySelectorAll(".erro").forEach((el) => (el.textContent = ""));
  feedback.textContent = "";
  feedback.className = "feedback";
}

function mostrarErroCampo(campo, mensagem) {
  const el = document.querySelector(`[data-erro="${campo}"]`);
  if (el) el.textContent = mensagem;
}

function validarFormulario(dados) {
  let valido = true;

  if (!dados.nome_completo.trim()) {
    mostrarErroCampo("nome_completo", "Informe o nome completo.");
    valido = false;
  }

  const cpfNumeros = dados.cpf.replace(/\D/g, "");
  if (cpfNumeros.length !== 11) {
    mostrarErroCampo("cpf", "CPF deve conter 11 dígitos.");
    valido = false;
  }

  if (!/^\S+@\S+\.\S+$/.test(dados.email)) {
    mostrarErroCampo("email", "E-mail inválido.");
    valido = false;
  }

  const telNumeros = dados.telefone.replace(/\D/g, "");
  if (telNumeros.length < 10 || telNumeros.length > 11) {
    mostrarErroCampo("telefone", "Telefone inválido.");
    valido = false;
  }

  if (dados.senha.length < 8) {
    mostrarErroCampo("senha", "A senha deve ter ao menos 8 caracteres.");
    valido = false;
  }

  const cepNumeros = dados.cep.replace(/\D/g, "");
  if (cepNumeros.length !== 8) {
    mostrarErroCampo("cep", "CEP deve conter 8 dígitos.");
    valido = false;
  }

  if (!dados.data_nascimento) {
    mostrarErroCampo("data_nascimento", "Informe a data de nascimento.");
    valido = false;
  }

  return valido;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  limparErros();

  const formData = new FormData(form);
  const dados = Object.fromEntries(formData.entries());

  if (!validarFormulario(dados)) {
    feedback.textContent = "Corrija os campos destacados antes de continuar.";
    feedback.classList.add("erro");
    return;
  }

  btnEnviar.disabled = true;
  btnEnviar.textContent = "Enviando...";

  try {
    const resposta = await fetch(`${API_URL}/adotantes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });

    const corpo = await resposta.json();

    if (!resposta.ok) {
      const mensagem = corpo.detail || "Não foi possível concluir o cadastro.";
      feedback.textContent = mensagem;
      feedback.classList.add("erro");
      return;
    }

    feedback.textContent = `Cadastro criado com sucesso! Bem-vindo(a), ${corpo.nome_completo}.`;
    feedback.classList.add("sucesso");
    form.reset();
  } catch (erro) {
    feedback.textContent = "Erro de conexão com o servidor. Tente novamente.";
    feedback.classList.add("erro");
    console.error(erro);
  } finally {
    btnEnviar.disabled = false;
    btnEnviar.textContent = "Criar cadastro";
  }
});

// Máscaras simples de digitação
document.getElementById("cpf").addEventListener("input", (e) => {
  e.target.value = e.target.value
    .replace(/\D/g, "")
    .slice(0, 11)
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
});

document.getElementById("cep").addEventListener("input", (e) => {
  e.target.value = e.target.value
    .replace(/\D/g, "")
    .slice(0, 8)
    .replace(/(\d{5})(\d)/, "$1-$2");
});
