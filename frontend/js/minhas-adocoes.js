// MatchPet - Minhas adoções (HU05 acompanhamento do pedido · HU06 envio de atualizações).
// Pedido aprovado = adoção concluída: libera o formulário com texto e foto (obrigatórios).

const sessao = Sessao.exigir();

const lista = document.getElementById("lista-solicitacoes");
const feedback = document.getElementById("feedback");
const TIPOS_FOTO = ["image/jpeg", "image/png", "image/webp"];
const LIMITE_FOTO = 5 * 1024 * 1024;

function montarFormulario(solicitacao, li) {
  const form = document.createElement("form");
  form.className = "form-acompanhamento";
  form.noValidate = true;
  form.innerHTML = `
    <div class="campo">
      <label>Como está a adaptação? *</label>
      <textarea name="descricao" rows="3" maxlength="1000"></textarea>
      <span class="erro" data-erro="descricao"></span>
    </div>
    <div class="campo">
      <label>Foto do animal * <small class="dica">JPG, PNG ou WEBP, até 5 MB</small></label>
      <input type="file" name="foto" accept="image/jpeg,image/png,image/webp" />
      <span class="erro" data-erro="foto"></span>
    </div>
    <p class="feedback" role="status"></p>
    <button type="submit">Enviar atualização</button>`;

  const erro = (campo, texto) => {
    form.querySelector(`[data-erro="${campo}"]`).textContent = texto;
    form.querySelector(`[name="${campo}"]`).classList.add("invalido");
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    form.querySelectorAll(".erro").forEach((el) => (el.textContent = ""));
    form.querySelectorAll(".invalido").forEach((el) => el.classList.remove("invalido"));
    const aviso = form.querySelector(".feedback");
    const descricao = form.descricao.value.trim();
    const foto = form.foto.files[0];
    let valido = true;
    if (!descricao) { erro("descricao", "Conte como está a adaptação do animal."); valido = false; }
    if (!foto) { erro("foto", "Envie uma foto do animal."); valido = false; }
    else if (!TIPOS_FOTO.includes(foto.type)) { erro("foto", "Envie a foto em JPG, PNG ou WEBP."); valido = false; }
    else if (foto.size > LIMITE_FOTO) { erro("foto", "A foto deve ter no máximo 5 MB."); valido = false; }
    if (!valido) { mensagemMP(aviso, "Preencha os campos destacados antes de enviar.", "erro"); return; }

    const dados = new FormData();
    dados.append("descricao", descricao);
    dados.append("foto", foto);
    const botao = form.querySelector("button");
    botao.disabled = true;
    botao.textContent = "Enviando...";
    try {
      const r = await fetch(`${API_URL}/solicitacoes/${solicitacao.id}/acompanhamentos`, {
        method: "POST", headers: Sessao.cabecalho(), body: dados,
      });
      const corpo = await r.json().catch(() => ({}));
      if (r.status === 401) { Sessao.sair(); return; }
      if (!r.ok) {
        if (Array.isArray(corpo.detail)) corpo.detail.forEach((e) => erro(e.campo, e.mensagem));
        mensagemMP(aviso, typeof corpo.detail === "string" ? corpo.detail : "Corrija os campos destacados.", "erro");
        return;
      }
      form.reset();
      mensagemMP(aviso, "Atualização registrada no histórico da adoção!", "sucesso");
      li.querySelector(".historico").replaceWith(await montarHistorico(solicitacao.id));
    } catch (e) {
      mensagemMP(aviso, "Erro de conexão com o servidor. Tente novamente.", "erro");
      console.error(e);
    } finally {
      botao.disabled = false;
      botao.textContent = "Enviar atualização";
    }
  });
  return form;
}

async function montarItem(s) {
  const li = document.createElement("li");
  li.className = "card-animal";
  const titulo = document.createElement("strong");
  titulo.textContent = s.animal_nome ?? `Animal ${s.animal_id}`;
  const selo = document.createElement("em");
  selo.className = `selo status-${s.status}`;
  selo.textContent = rotuloMP(s.status);
  const data = document.createElement("span");
  data.textContent = `Pedido feito em ${formatarDataHoraMP(s.criado_em)}`;
  li.append(titulo, selo, data);
  comFoto(li, s.animal_foto_url, null, s.animal_nome);
  if (s.status === "aprovada") {
    const h = document.createElement("h3");
    h.textContent = "Acompanhamento pós-adoção";
    li.querySelector(".card-corpo").append(h, montarFormulario(s, li), await montarHistorico(s.id));
  }
  return li;
}

async function carregar() {
  if (!sessao) return;
  try {
    const r = await fetch(`${API_URL}/solicitacoes?adotante_id=${sessao.adotante_id}`);
    if (!r.ok) throw new Error(r.status);
    const solicitacoes = await r.json();
    lista.replaceChildren(...(await Promise.all(solicitacoes.map(montarItem))));
    mensagemMP(feedback, solicitacoes.length ? "" : "Você ainda não fez nenhum pedido de adoção.", "");
  } catch (e) {
    mensagemMP(feedback, "Não foi possível carregar os seus pedidos. Tente novamente.", "erro");
    console.error(e);
  }
}

carregar();
