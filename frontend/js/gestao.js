// MatchPet - Área do responsável.
// HU05: o responsável aprova (adoção concluída) ou recusa (o animal volta a ficar disponível).
// HU06, cenário 2: o responsável consulta o histórico de cada adoção concluída.

const feedback = document.getElementById("feedback");
const pendentes = document.getElementById("lista-pendentes");
const aprovadas = document.getElementById("lista-aprovadas");

function cabecalhoItem(s) {
  const titulo = document.createElement("strong");
  titulo.textContent = `${s.animal_nome} · adotante: ${s.adotante_nome}`;
  const data = document.createElement("span");
  data.textContent = `Pedido feito em ${formatarDataHoraMP(s.criado_em)}`;
  return [titulo, data];
}

function itemPendente(s) {
  const li = document.createElement("li");
  li.className = "card-animal";
  li.append(...cabecalhoItem(s));
  comFoto(li, s.animal_foto_url, null, s.animal_nome);
  const corpo = li.querySelector(".card-corpo");
  const area = document.createElement("div");
  area.className = "acao-adotar";
  for (const [status, texto, classe] of [["aprovada", "Aprovar adoção", ""], ["recusada", "Recusar", "secundario"]]) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = texto;
    if (classe) b.className = classe;
    b.addEventListener("click", () => decidir(s.id, status));
    area.append(b);
  }
  corpo.append(area);
  return li;
}

async function itemAprovado(s) {
  const li = document.createElement("li");
  li.className = "card-animal";
  li.append(...cabecalhoItem(s));
  comFoto(li, s.animal_foto_url, null, s.animal_nome);
  li.querySelector(".card-corpo").append(await montarHistorico(s.id));
  return li;
}

async function decidir(id, status) {
  try {
    const r = await fetch(`${API_URL}/solicitacoes/${id}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }),
    });
    if (!r.ok) throw new Error(r.status);
    await carregar();
    mensagemMP(feedback, status === "aprovada" ? "Adoção aprovada." : "Pedido recusado; o animal voltou para a lista de disponíveis.", "sucesso");
  } catch (e) {
    mensagemMP(feedback, "Não foi possível registrar a decisão. Tente novamente.", "erro");
    console.error(e);
  }
}

async function carregar() {
  try {
    const [p, a] = await Promise.all([
      fetch(`${API_URL}/solicitacoes?status=pendente`).then((r) => r.json()),
      fetch(`${API_URL}/solicitacoes?status=aprovada`).then((r) => r.json()),
    ]);
    pendentes.replaceChildren(...p.map(itemPendente));
    aprovadas.replaceChildren(...(await Promise.all(a.map(itemAprovado))));
    if (!p.length) pendentes.innerHTML = '<li class="vazio">Nenhum pedido aguardando análise.</li>';
    if (!a.length) aprovadas.innerHTML = '<li class="vazio">Nenhuma adoção concluída ainda.</li>';
    mensagemMP(feedback, "", "");
  } catch (e) {
    mensagemMP(feedback, "Não foi possível carregar os pedidos. Tente novamente.", "erro");
    console.error(e);
  }
}

carregar();
