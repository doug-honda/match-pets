// MatchPet - Perfil de Adoção (HU03)
// Lê ?id= da URL (adotante), carrega o perfil salvo (GET) e salva com PUT.
// Cenário 1: salvar o perfil. Cenário 2: bloquear e destacar campos vazios.
// Cenário 3: com perfil já salvo, o formulário vem preenchido e o PUT substitui os dados.


const form = document.getElementById("form-perfil");
const feedback = document.getElementById("feedback");
const feedbackCarga = document.getElementById("feedback-carga");
const btnSalvar = document.getElementById("btn-salvar");
const linkPerfil = document.getElementById("link-perfil");

const CAMPOS = {
  tipo_moradia: "Selecione o tipo de moradia.",
  tem_criancas: "Informe se há crianças na casa.",
  tem_outros_animais: "Informe se há outros animais na casa.",
  nivel_atividade: "Selecione o seu nível de atividade.",
  horas_sozinho: "Informe quantas horas o animal ficará sozinho.",
  ja_teve_pet: "Informe se já teve animal de estimação.",
  especie_preferida: "Selecione a espécie preferida.",
  porte_preferido: "Selecione o porte preferido.",
};
const CAMPOS_BOOLEANOS = ["tem_criancas", "tem_outros_animais", "ja_teve_pet"];

const adotanteId = new URLSearchParams(window.location.search).get("id");
let perfilExiste = false;

function mensagem(el, texto, tipo) {
  el.textContent = texto;
  el.className = `feedback ${tipo}`;
}

function limparErros() {
  document.querySelectorAll(".erro").forEach((el) => (el.textContent = ""));
  form.querySelectorAll(".invalido").forEach((el) => el.classList.remove("invalido"));
  mensagem(feedback, "", "");
}

function marcarErro(campo, texto) {
  const span = document.querySelector(`[data-erro="${campo}"]`);
  if (span) span.textContent = texto;
  const entrada = document.getElementById(campo);
  if (entrada) entrada.classList.add("invalido");
}

function validar(dados) {
  let valido = true;
  for (const [campo, texto] of Object.entries(CAMPOS)) {
    if (!String(dados[campo] ?? "").trim()) {
      marcarErro(campo, texto);
      valido = false;
    }
  }
  return valido;
}

// Erro 422 do FastAPI chega como lista; cada item aponta o campo em "loc".
function mostrarErroApi(corpo) {
  const detalhe = corpo && corpo.detail;
  if (Array.isArray(detalhe)) {
    detalhe.forEach((erro) => {
      const campo = Array.isArray(erro.loc) ? erro.loc[erro.loc.length - 1] : null;
      if (campo && CAMPOS[campo]) marcarErro(campo, CAMPOS[campo]);
    });
    return "Responda os campos destacados antes de salvar.";
  }
  return typeof detalhe === "string" ? detalhe : "Não foi possível salvar o perfil.";
}

function paraApi(dados) {
  const corpo = { ...dados };
  for (const campo of CAMPOS_BOOLEANOS) corpo[campo] = dados[campo] === "true";
  return corpo;
}

function preencher(perfil) {
  for (const campo of Object.keys(CAMPOS)) {
    document.getElementById(campo).value = String(perfil[campo]);
  }
}

function modoEdicao(ativo) {
  perfilExiste = ativo;
  btnSalvar.textContent = ativo ? "Atualizar perfil" : "Salvar perfil";
}

async function carregar() {
  if (!/^\d+$/.test(adotanteId || "")) {
    mensagem(feedbackCarga, "Cadastro não encontrado.", "erro");
    return;
  }
  if (linkPerfil) linkPerfil.href = `perfil.html?id=${encodeURIComponent(adotanteId)}`;

  try {
    const resposta = await fetch(`${API_URL}/adotantes/${adotanteId}/perfil`);
    const corpo = await resposta.json().catch(() => ({}));
    if (resposta.ok) {
      preencher(corpo);
      modoEdicao(true);
    } else if (resposta.status === 404 && corpo.detail === "Perfil ainda não preenchido.") {
      modoEdicao(false);
    } else if (resposta.status === 404) {
      mensagem(feedbackCarga, "Cadastro não encontrado.", "erro");
      return;
    } else {
      mensagem(feedbackCarga, "Não foi possível carregar o perfil. Tente novamente.", "erro");
      return;
    }
    form.hidden = false;
  } catch (erro) {
    mensagem(feedbackCarga, "Erro de conexão com o servidor. Tente novamente.", "erro");
    console.error(erro);
  }
}

form.addEventListener("change", (event) => {
  // Ao responder um campo destacado, remove o destaque dele.
  if (event.target.value) {
    event.target.classList.remove("invalido");
    const span = document.querySelector(`[data-erro="${event.target.id}"]`);
    if (span) span.textContent = "";
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  limparErros();

  const dados = Object.fromEntries(new FormData(form).entries());
  if (!validar(dados)) {
    mensagem(feedback, "Responda os campos destacados antes de salvar.", "erro");
    return;
  }

  const atualizando = perfilExiste;
  btnSalvar.disabled = true;
  btnSalvar.textContent = "Salvando...";
  try {
    const resposta = await fetch(`${API_URL}/adotantes/${adotanteId}/perfil`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(paraApi(dados)),
    });
    const corpo = await resposta.json().catch(() => ({}));
    if (!resposta.ok) {
      mensagem(feedback, mostrarErroApi(corpo), "erro");
      modoEdicao(atualizando);
      return;
    }
    preencher(corpo);
    modoEdicao(true);
    mensagem(feedback, atualizando ? "Perfil atualizado com sucesso!" : "Perfil salvo com sucesso!", "sucesso");
  } catch (erro) {
    mensagem(feedback, "Erro de conexão com o servidor. Tente novamente.", "erro");
    modoEdicao(atualizando);
    console.error(erro);
  } finally {
    btnSalvar.disabled = false;
  }
});

carregar();
