// MatchPet - Animais disponíveis (visão do adotante, somente leitura)
// Consome GET /animais?disponivel=true: animais marcados como indisponíveis não aparecem.


const lista = document.getElementById("lista-animais");
const mensagem = document.getElementById("lista-vazia");

const ROTULOS = {
  cao: "Cão", gato: "Gato",
  pequeno: "Pequeno", medio: "Médio", grande: "Grande",
  baixo: "Baixo", alto: "Alto", baixa: "Baixa", media: "Média", alta: "Alta",
};
const rotulo = (v) => ROTULOS[v] ?? v;
const simNao = (b) => (b ? "Sim" : "Não");

function montarCard(a) {
  const li = document.createElement("li");
  li.className = "card-animal";

  const titulo = document.createElement("strong");
  titulo.textContent =
    `${a.nome} · ${rotulo(a.especie)} ${rotulo(a.porte).toLowerCase()}, ` +
    `${a.idade_anos} ${a.idade_anos === 1 ? "ano" : "anos"}`;

  const detalhes = document.createElement("span");
  detalhes.textContent =
    `Nível de energia: ${rotulo(a.nivel_energia).toLowerCase()} · ` +
    `Sozinho: tolerância ${rotulo(a.tolerancia_sozinho).toLowerCase()} · ` +
    `Crianças: ${simNao(a.convive_criancas)} · Outros animais: ${simNao(a.convive_outros_animais)} · ` +
    `Exige experiência: ${simNao(a.exige_experiencia)}`;

  li.append(titulo, detalhes);
  if (a.descricao) {
    const descricao = document.createElement("span");
    descricao.textContent = a.descricao;
    li.append(descricao);
  }
  return comFoto(li, a.foto_url, a.especie, a.nome);
}

async function carregar() {
  try {
    const resposta = await fetch(`${API_URL}/animais?disponivel=true`);
    if (!resposta.ok) throw new Error(resposta.status);
    const animais = await resposta.json();
    lista.replaceChildren(...animais.map(montarCard));
    mensagem.textContent = "Nenhum animal disponível no momento.";
    mensagem.hidden = animais.length > 0;
  } catch (erro) {
    mensagem.hidden = false;
    mensagem.textContent = "Não foi possível carregar os animais. Tente novamente.";
    console.error(erro);
  }
}

carregar();
