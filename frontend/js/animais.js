// MatchPet - Cadastro de Animais (HU02)
// Integração da interface com a API (FastAPI)


const form = document.getElementById("form-animal");
const feedback = document.getElementById("feedback");
const btnEnviar = document.getElementById("btn-enviar");
const lista = document.getElementById("lista-animais");
const listaVazia = document.getElementById("lista-vazia");
const listaIndisponiveis = document.getElementById("lista-indisponiveis");
const secaoIndisponiveis = document.getElementById("secao-indisponiveis");

const ROTULOS = {
  cao: "Cão", gato: "Gato",
  pequeno: "Pequeno", medio: "Médio", grande: "Grande",
  baixo: "Baixo", alto: "Alto", baixa: "Baixa", media: "Média", alta: "Alta",
};
const rotulo = (v) => ROTULOS[v] ?? v;
const simNao = (b) => (b ? "Sim" : "Não");

const OBRIGATORIOS = {
  nome: "Informe o nome do animal.",
  especie: "Selecione a espécie.",
  porte: "Selecione o porte.",
  idade_anos: "Informe a idade (0 a 30 anos).",
  nivel_energia: "Selecione o nível de energia.",
  tolerancia_sozinho: "Selecione a tolerância a ficar sozinho.",
  convive_criancas: "Informe se convive bem com crianças.",
  convive_outros_animais: "Informe se convive bem com outros animais.",
  exige_experiencia: "Informe se exige tutor com experiência.",
  disponivel: "Informe se está disponível para adoção.",
};

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
  for (const [campo, mensagem] of Object.entries(OBRIGATORIOS)) {
    if (!String(dados[campo] ?? "").trim()) {
      mostrarErroCampo(campo, mensagem);
      valido = false;
    }
  }
  const idade = Number(dados.idade_anos);
  if (String(dados.idade_anos ?? "").trim() && !(Number.isInteger(idade) && idade >= 0 && idade <= 30)) {
    mostrarErroCampo("idade_anos", "A idade deve ser um número inteiro de 0 a 30.");
    valido = false;
  }
  return valido;
}

// Erro 422 do FastAPI chega como lista; cada item aponta o campo em "loc".
function mostrarErroApi(corpo) {
  const detalhe = corpo && corpo.detail;
  if (Array.isArray(detalhe)) {
    detalhe.forEach((erro) => {
      const campo = Array.isArray(erro.loc) ? erro.loc[erro.loc.length - 1] : null;
      const mensagem = (erro.msg || "Valor inválido.").replace(/^Value error, /, "");
      if (campo) mostrarErroCampo(campo, mensagem);
    });
    return "Corrija os campos destacados antes de continuar.";
  }
  return typeof detalhe === "string" ? detalhe : "Não foi possível cadastrar o animal.";
}

function montarCard(a) {
  const li = document.createElement("li");
  li.className = "card-animal";

  const titulo = document.createElement("strong");
  titulo.textContent = `${a.nome} · ${rotulo(a.especie)} ${rotulo(a.porte).toLowerCase()}, ${a.idade_anos} ${a.idade_anos === 1 ? "ano" : "anos"}`;

  const detalhes = document.createElement("span");
  detalhes.textContent =
    `Nível de energia: ${rotulo(a.nivel_energia).toLowerCase()} · ` +
    `Sozinho: tolerância ${rotulo(a.tolerancia_sozinho).toLowerCase()} · ` +
    `Crianças: ${simNao(a.convive_criancas)} · Outros animais: ${simNao(a.convive_outros_animais)} · ` +
    `Exige experiência: ${simNao(a.exige_experiencia)}`;

  const selo = document.createElement("em");
  selo.className = a.disponivel ? "selo disponivel" : "selo indisponivel";
  selo.textContent = a.disponivel ? "Disponível" : "Indisponível";

  const botao = document.createElement("button");
  botao.type = "button";
  botao.textContent = a.disponivel ? "Marcar como indisponível" : "Marcar como disponível";
  botao.addEventListener("click", () => alterarDisponibilidade(a.id, !a.disponivel));

  li.append(titulo, detalhes, selo, botao);
  return comFoto(li, a.foto_url, a.especie, a.nome);
}

async function carregarLista() {
  try {
    const resposta = await fetch(`${API_URL}/animais`);
    if (!resposta.ok) throw new Error(resposta.status);
    const animais = await resposta.json();
    const disponiveis = animais.filter((a) => a.disponivel);
    const indisponiveis = animais.filter((a) => !a.disponivel);
    lista.replaceChildren(...disponiveis.map(montarCard));
    listaIndisponiveis.replaceChildren(...indisponiveis.map(montarCard));
    listaVazia.textContent = "Nenhum animal disponível no momento.";
    listaVazia.hidden = disponiveis.length > 0;
    secaoIndisponiveis.hidden = indisponiveis.length === 0;
  } catch (erro) {
    listaVazia.hidden = false;
    listaVazia.textContent = "Não foi possível carregar a lista de animais.";
    console.error(erro);
  }
}

// HU02, cenário 3: ao ficar indisponível, o animal sai da lista de disponíveis.
async function alterarDisponibilidade(id, disponivel) {
  try {
    const resposta = await fetch(`${API_URL}/animais/${id}/disponibilidade`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ disponivel }),
    });
    if (!resposta.ok) throw new Error(resposta.status);
    await carregarLista();
  } catch (erro) {
    feedback.textContent = "Não foi possível alterar a disponibilidade. Tente novamente.";
    feedback.className = "feedback erro";
    console.error(erro);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  limparErros();

  const dados = Object.fromEntries(new FormData(form).entries());

  if (!validarFormulario(dados)) {
    feedback.textContent = "Corrija os campos destacados antes de continuar.";
    feedback.classList.add("erro");
    return;
  }

  const corpoEnvio = {
    ...dados,
    convive_criancas: dados.convive_criancas === "true",
    convive_outros_animais: dados.convive_outros_animais === "true",
    exige_experiencia: dados.exige_experiencia === "true",
    disponivel: dados.disponivel === "true",
  };

  btnEnviar.disabled = true;
  btnEnviar.textContent = "Enviando...";

  try {
    const resposta = await fetch(`${API_URL}/animais`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpoEnvio),
    });
    const corpo = await resposta.json().catch(() => ({}));

    if (!resposta.ok) {
      feedback.textContent = mostrarErroApi(corpo);
      feedback.classList.add("erro");
      return;
    }

    // Foto opcional: enviada depois que o animal já existe.
    const foto = document.getElementById("foto_animal").files[0];
    let avisoFoto = "";
    if (foto) {
      const envio = new FormData();
      envio.append("foto", foto);
      const r = await fetch(`${API_URL}/animais/${corpo.id}/foto`, { method: "POST", body: envio });
      if (!r.ok) {
        const erroFoto = await r.json().catch(() => ({}));
        avisoFoto = ` A foto não foi salva: ${erroFoto.detail?.[0]?.mensagem ?? "tente outra imagem"}.`;
      }
    }

    feedback.textContent = `Animal cadastrado com sucesso: ${corpo.nome}.${avisoFoto}`;
    feedback.classList.add(avisoFoto ? "erro" : "sucesso");
    form.reset();
    await carregarLista();
  } catch (erro) {
    feedback.textContent = "Erro de conexão com o servidor. Tente novamente.";
    feedback.classList.add("erro");
    console.error(erro);
  } finally {
    btnEnviar.disabled = false;
    btnEnviar.textContent = "Cadastrar animal";
  }
});

carregarLista();
