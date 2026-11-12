// MatchPet - Perfil do Adotante
// Lê ?id= da URL e consulta GET /adotantes/{id}. A API não devolve a senha;
// a tela também não a exibe.


const feedback = document.getElementById("feedback-perfil");
const perfil = document.getElementById("perfil");

function mostrarMensagem(texto, tipo) {
  feedback.textContent = texto;
  feedback.className = `feedback ${tipo}`;
}

function mascararCpf(cpf) {
  const n = String(cpf).replace(/\D/g, "");
  if (n.length !== 11) return "***.***.***-**";
  return `***.${n.slice(3, 6)}.${n.slice(6, 9)}-**`;
}

function formatarTelefone(tel) {
  const n = String(tel).replace(/\D/g, "");
  if (n.length === 11) return `(${n.slice(0, 2)}) ${n.slice(2, 7)}-${n.slice(7)}`;
  if (n.length === 10) return `(${n.slice(0, 2)}) ${n.slice(2, 6)}-${n.slice(6)}`;
  return tel;
}

// "AAAA-MM-DD" -> "DD/MM/AAAA" sem passar por Date (evita deslocamento de fuso).
function formatarData(iso) {
  const [ano, mes, dia] = String(iso).slice(0, 10).split("-");
  return `${dia}/${mes}/${ano}`;
}

function formatarDataHora(iso) {
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return iso;
  return data.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

function preencher(a) {
  const logradouro = [a.logradouro, a.numero].filter(Boolean).join(", ");
  const comComplemento = a.complemento ? `${logradouro} - ${a.complemento}` : logradouro;

  const campos = {
    "p-nome": a.nome_completo,
    "p-cpf": mascararCpf(a.cpf),
    "p-nascimento": formatarData(a.data_nascimento),
    "p-email": a.email,
    "p-telefone": formatarTelefone(a.telefone),
    "p-logradouro": comComplemento,
    "p-bairro": a.bairro,
    "p-cidade": `${a.cidade} / ${a.estado}`,
    "p-cep": a.cep,
    "p-criado-em": formatarDataHora(a.criado_em),
  };
  // textContent (nunca innerHTML): os dados vêm do usuário.
  for (const [id, valor] of Object.entries(campos)) {
    document.getElementById(id).textContent = valor;
  }
  perfil.hidden = false;
}

// Liga o link do perfil de adoção (HU03) ao adotante exibido.
function ligarPerfilAdocao(id) {
  const link = document.getElementById("link-perfil-adocao");
  if (link) link.href = `perfil-adocao.html?id=${encodeURIComponent(id)}`;
}

async function carregarPerfil() {
  const id = new URLSearchParams(window.location.search).get("id");
  if (!/^\d+$/.test(id || "")) {
    mostrarMensagem("Cadastro não encontrado.", "erro");
    return;
  }

  mostrarMensagem("Carregando perfil...", "");
  try {
    const resposta = await fetch(`${API_URL}/adotantes/${id}`);
    if (resposta.status === 404) {
      mostrarMensagem("Cadastro não encontrado.", "erro");
      return;
    }
    if (!resposta.ok) {
      mostrarMensagem("Não foi possível carregar o perfil. Tente novamente.", "erro");
      return;
    }
    preencher(await resposta.json());
    ligarPerfilAdocao(id);
    mostrarMensagem("", "");
  } catch (erro) {
    mostrarMensagem("Erro de conexão com o servidor. Tente novamente.", "erro");
    console.error(erro);
  }
}

carregarPerfil();
