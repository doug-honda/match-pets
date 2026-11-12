// MatchPet - HU04 (compatibilidade) e HU05 (solicitação de adoção).
// GET /adotantes/{id}/compatibilidade -> animais ordenados pela nota, com destaque para nota >= 75.
// Perfil incompleto (409): mostra o aviso e o link para completar o perfil (cenário 3 da HU04).
// "Quero adotar" -> confirmação -> POST /solicitacoes (cenários 1 a 3 da HU05).

const sessao = Sessao.exigir();

const lista = document.getElementById("lista-compativeis");
const feedback = document.getElementById("feedback");
const NOMES_CRITERIOS = {
  espaco_porte: "Espaço × porte",
  atividade_energia: "Atividade × energia",
  sozinho_tolerancia: "Tempo sozinho × tolerância",
  experiencia: "Experiência",
  porte_preferido: "Porte preferido",
};
const ROTULO_FAIXA = { alta: "Alta compatibilidade", media: "Média compatibilidade", baixa: "Baixa compatibilidade" };

function montarCard(item) {
  const a = item.animal;
  const li = document.createElement("li");
  li.className = `card-animal${item.destaque ? " destaque" : ""}`;

  const topo = document.createElement("div");
  topo.className = "card-topo";
  const titulo = document.createElement("strong");
  titulo.textContent = `${a.nome} · ${rotuloMP(a.especie)} ${rotuloMP(a.porte).toLowerCase()}, ${a.idade_anos} ${a.idade_anos === 1 ? "ano" : "anos"}`;
  const nota = document.createElement("b");
  nota.className = "nota";
  nota.textContent = `${item.nota}/100`;
  topo.append(titulo, nota);

  const barra = document.createElement("div");
  barra.className = "barra";
  const preenchida = document.createElement("i");
  preenchida.style.width = `${item.nota}%`;
  barra.append(preenchida);

  const selo = document.createElement("em");
  selo.className = `selo faixa-${item.faixa}`;
  selo.textContent = (item.destaque ? "★ " : "") + ROTULO_FAIXA[item.faixa];

  const detalhe = document.createElement("span");
  detalhe.textContent = Object.entries(item.pontos_por_criterio)
    .map(([codigo, pontos]) => `${NOMES_CRITERIOS[codigo] ?? codigo}: ${pontos}`)
    .join(" · ");

  li.append(topo, barra, selo, detalhe);
  if (a.descricao) {
    const descricao = document.createElement("span");
    descricao.textContent = a.descricao;
    li.append(descricao);
  }
  li.append(montarAcaoAdotar(a, li));
  return comFoto(li, a.foto_url, a.especie, a.nome);
}

// HU05: "selecionar a opção de solicitar adoção e confirmar".
function montarAcaoAdotar(animal, li) {
  const area = document.createElement("div");
  area.className = "acao-adotar";
  const btn = document.createElement("button");
  btn.type = "button";
  btn.textContent = "Quero adotar";
  const resposta = document.createElement("p");
  resposta.className = "feedback";

  btn.addEventListener("click", () => {
    area.replaceChildren();
    const pergunta = document.createElement("span");
    pergunta.textContent = `Confirmar o pedido de adoção de ${animal.nome}?`;
    const sim = document.createElement("button");
    sim.type = "button";
    sim.textContent = "Confirmar";
    const nao = document.createElement("button");
    nao.type = "button";
    nao.className = "secundario";
    nao.textContent = "Cancelar";
    nao.addEventListener("click", () => area.replaceChildren(btn, resposta));
    sim.addEventListener("click", () => solicitar(animal, area, sim, nao, resposta, li));
    area.append(pergunta, sim, nao, resposta);
  });
  area.append(btn, resposta);
  return area;
}

async function solicitar(animal, area, sim, nao, resposta, li) {
  sim.disabled = true;
  nao.disabled = true;
  try {
    const r = await fetch(`${API_URL}/solicitacoes`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...Sessao.cabecalho() },
      body: JSON.stringify({ adotante_id: sessao.adotante_id, animal_id: animal.id }),
    });
    const corpo = await r.json().catch(() => ({}));
    if (r.status === 401) { Sessao.sair(); return; }
    if (r.ok) {
      const ok = document.createElement("p");
      ok.className = "feedback sucesso";
      ok.textContent = `Pedido enviado! O seu interesse em adotar ${animal.nome} foi registrado. Acompanhe em "Minhas adoções".`;
      area.replaceChildren(ok);
      li.classList.add("solicitado");
      return;
    }
    const erro = document.createElement("p");
    erro.className = "feedback erro";
    erro.textContent = r.status === 409 ? `${animal.nome} não está mais disponível para adoção.` : (corpo.detail || "Não foi possível enviar o pedido.");
    area.replaceChildren(erro);
  } catch (e) {
    mensagemMP(resposta, "Erro de conexão com o servidor. Tente novamente.", "erro");
    sim.disabled = false;
    nao.disabled = false;
    console.error(e);
  }
}

async function carregarCriterios() {
  try {
    const criterios = await (await fetch(`${API_URL}/criterios-compatibilidade`)).json();
    const ul = document.getElementById("lista-criterios");
    ul.replaceChildren(...criterios.map((c) => {
      const li = document.createElement("li");
      li.textContent = c.tipo === "eliminatorio" ? `Filtro · ${c.nome}: ${c.descricao}` : `${c.nome} (até ${c.peso} pontos): ${c.descricao}`;
      return li;
    }));
  } catch (e) {
    console.error(e);
  }
}

async function carregar() {
  if (!sessao) return;
  try {
    const r = await fetch(`${API_URL}/adotantes/${sessao.adotante_id}/compatibilidade`);
    const corpo = await r.json().catch(() => ({}));
    if (r.status === 409) {
      mensagemMP(feedback, corpo.detail.mensagem, "erro");
      document.getElementById("a-completar").href = `perfil-adocao.html?id=${sessao.adotante_id}`;
      document.getElementById("link-completar").hidden = false;
      return;
    }
    if (!r.ok) throw new Error(r.status);
    lista.replaceChildren(...corpo.animais.map(montarCard));
    mensagemMP(feedback, corpo.animais.length ? "" : "Nenhum animal disponível combina com o seu perfil no momento.", "");
    const n = corpo.eliminados;
    document.getElementById("eliminados").textContent =
      n === 0 ? "" : n === 1
        ? "1 animal não aparece porque não combina com a sua casa ou não está disponível."
        : `${n} animais não aparecem porque não combinam com a sua casa ou não estão disponíveis.`;
  } catch (e) {
    mensagemMP(feedback, "Não foi possível calcular a compatibilidade. Tente novamente.", "erro");
    console.error(e);
  }
}

carregarCriterios();
carregar();
