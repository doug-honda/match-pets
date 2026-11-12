"""
MatchPet API
Sprint 1 - HU01: Cadastro do Adotante · HU02: Cadastro do Animal · HU03: Perfil do Adotante
Sprint 2 - HU04: Compatibilidade · HU05: Solicitação de adoção · HU06: Acompanhamento pós-adoção
"""
import os
import secrets
import uuid
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status, Header, Form, File, UploadFile, Query
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import bcrypt

from database import engine, get_db, Base
import models
import schemas
import compatibilidade

# Cria as tabelas (em produção, prefira migrations com Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MatchPet API", version="0.4.0")

# CORS liberado para o front-end local (ajustar em produção)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def gerar_hash_senha(senha: str) -> str:
    """Gera o hash da senha com bcrypt (a senha em texto puro nunca é salva)."""
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@app.get("/", include_in_schema=False)
def pagina_inicial():
    """Quem abre o endereço da API cai na tela inicial do sistema."""
    return RedirectResponse(url="/inicio.html")


@app.get("/status")
def health_check():
    return {"status": "ok", "service": "MatchPet API"}


@app.post(
    "/adotantes",
    response_model=schemas.AdotanteResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Adotante"],
)
def criar_adotante(dados: schemas.AdotanteCreate, db: Session = Depends(get_db)):
    """
    Cria o cadastro de um novo adotante.
    Cobre: HU01 (cadastro), validação de CPF/e-mail únicos e senha com hash.
    """
    # CA3: e-mail (ou CPF) já cadastrado -> bloqueia com mensagem específica
    if db.query(models.Adotante).filter(models.Adotante.email == dados.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"campo": "email", "mensagem": "Este e-mail já está em uso."},
        )
    if db.query(models.Adotante).filter(models.Adotante.cpf == dados.cpf).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"campo": "cpf", "mensagem": "Este CPF já está cadastrado."},
        )

    senha_hash = gerar_hash_senha(dados.senha)

    novo_adotante = models.Adotante(
        nome_completo=dados.nome_completo,
        cpf=dados.cpf,
        email=dados.email,
        telefone=dados.telefone,
        data_nascimento=dados.data_nascimento,
        senha_hash=senha_hash,
        cep=dados.cep,
        logradouro=dados.logradouro,
        numero=dados.numero,
        complemento=dados.complemento,
        bairro=dados.bairro,
        cidade=dados.cidade,
        estado=dados.estado,
    )

    db.add(novo_adotante)
    try:
        db.commit()
        db.refresh(novo_adotante)
    except IntegrityError:
        # Proteção extra caso dois cadastros iguais cheguem ao mesmo tempo
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF ou e-mail já cadastrado.",
        )

    return novo_adotante


@app.get(
    "/adotantes/{adotante_id}",
    response_model=schemas.AdotanteResponse,
    tags=["Adotante"],
)
def buscar_adotante(adotante_id: int, db: Session = Depends(get_db)):
    """Busca um adotante pelo ID (útil para telas de perfil/edição)."""
    adotante = db.query(models.Adotante).filter(models.Adotante.id == adotante_id).first()
    if not adotante:
        raise HTTPException(status_code=404, detail="Adotante não encontrado.")
    return adotante


@app.post(
    "/animais",
    response_model=schemas.AnimalResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Animal"],
)
def criar_animal(dados: schemas.AnimalCreate, db: Session = Depends(get_db)):
    """Cadastra um animal disponível para adoção (HU02)."""
    animal = models.Animal(**dados.model_dump())
    db.add(animal)
    db.commit()
    db.refresh(animal)
    return animal


@app.get("/animais", response_model=list[schemas.AnimalResponse], tags=["Animal"])
def listar_animais(disponivel: bool | None = None, db: Session = Depends(get_db)):
    """Lista os animais. Com ?disponivel=true, só os disponíveis para adoção (o que o adotante vê)."""
    consulta = db.query(models.Animal)
    if disponivel is not None:
        consulta = consulta.filter(models.Animal.disponivel == disponivel)
    return consulta.order_by(models.Animal.id).all()


@app.get("/animais/{animal_id}", response_model=schemas.AnimalResponse, tags=["Animal"])
def buscar_animal(animal_id: int, db: Session = Depends(get_db)):
    animal = db.query(models.Animal).filter(models.Animal.id == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado.")
    return animal


@app.patch(
    "/animais/{animal_id}/disponibilidade",
    response_model=schemas.AnimalResponse,
    tags=["Animal"],
)
def alterar_disponibilidade(
    animal_id: int, dados: schemas.AnimalDisponibilidade, db: Session = Depends(get_db)
):
    """Marca o animal como disponível ou indisponível para adoção (HU02, cenário 3)."""
    animal = db.query(models.Animal).filter(models.Animal.id == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado.")
    animal.disponivel = dados.disponivel
    db.commit()
    db.refresh(animal)
    return animal


def obter_adotante_ou_404(adotante_id: int, db: Session) -> models.Adotante:
    adotante = db.query(models.Adotante).filter(models.Adotante.id == adotante_id).first()
    if not adotante:
        raise HTTPException(status_code=404, detail="Adotante não encontrado.")
    return adotante


@app.get(
    "/adotantes/{adotante_id}/perfil",
    response_model=schemas.PerfilAdotanteResponse,
    tags=["Perfil do adotante"],
)
def buscar_perfil(adotante_id: int, db: Session = Depends(get_db)):
    """Retorna o perfil de adoção do adotante (HU03). 404 se ainda não foi preenchido."""
    obter_adotante_ou_404(adotante_id, db)
    perfil = (
        db.query(models.PerfilAdotante)
        .filter(models.PerfilAdotante.adotante_id == adotante_id)
        .first()
    )
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil ainda não preenchido.")
    return perfil


@app.put(
    "/adotantes/{adotante_id}/perfil",
    response_model=schemas.PerfilAdotanteResponse,
    tags=["Perfil do adotante"],
)
def salvar_perfil(
    adotante_id: int, dados: schemas.PerfilAdotanteDados, db: Session = Depends(get_db)
):
    """
    Cria ou atualiza o perfil de adoção (HU03).
    Cenário 1: salva o perfil. Cenário 2: campos ausentes ou inválidos -> 422.
    Cenário 3: se já existe, substitui os dados anteriores.
    """
    obter_adotante_ou_404(adotante_id, db)
    perfil = (
        db.query(models.PerfilAdotante)
        .filter(models.PerfilAdotante.adotante_id == adotante_id)
        .first()
    )
    if perfil is None:
        perfil = models.PerfilAdotante(adotante_id=adotante_id, **dados.model_dump())
        db.add(perfil)
    else:
        for campo, valor in dados.model_dump().items():
            setattr(perfil, campo, valor)
    db.commit()
    db.refresh(perfil)
    return perfil


# =====================================================================
# Login (HU05: "Dado que o adotante está autenticado")
# =====================================================================
@app.post("/login", response_model=schemas.LoginResponse, tags=["Login"])
def login(dados: schemas.LoginDados, db: Session = Depends(get_db)):
    """Confere e-mail e senha e abre uma sessão. O token vai no cabeçalho Authorization."""
    adotante = db.query(models.Adotante).filter(models.Adotante.email == dados.email).first()
    senha_ok = adotante is not None and bcrypt.checkpw(
        dados.senha.encode("utf-8"), adotante.senha_hash.encode("utf-8")
    )
    if not senha_ok:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    token = secrets.token_hex(32)
    db.add(models.Sessao(token=token, adotante_id=adotante.id))
    db.commit()
    return {"adotante_id": adotante.id, "nome_completo": adotante.nome_completo, "token": token}


def adotante_logado(
    authorization: str | None = Header(default=None), db: Session = Depends(get_db)
) -> models.Adotante:
    """Lê "Authorization: Bearer <token>" e devolve o adotante da sessão (401 sem login)."""
    token = (authorization or "").removeprefix("Bearer ").strip()
    sessao = db.get(models.Sessao, token) if token else None
    if sessao is None:
        raise HTTPException(status_code=401, detail="Faça login para continuar.")
    return obter_adotante_ou_404(sessao.adotante_id, db)


# =====================================================================
# HU04 - Compatibilidade entre adotante e animal
# =====================================================================
CAMPOS_PERFIL = list(schemas.PerfilAdotanteDados.model_fields)


@app.get("/criterios-compatibilidade", response_model=list[schemas.CriterioResponse], tags=["Compatibilidade"])
def listar_criterios(db: Session = Depends(get_db)):
    """Os 9 critérios do cálculo (4 eliminatórios e 5 de pontuação) com os pesos gravados no banco."""
    return compatibilidade.garantir_criterios(db)


@app.get(
    "/adotantes/{adotante_id}/compatibilidade",
    response_model=schemas.CompatibilidadeResponse,
    tags=["Compatibilidade"],
)
def consultar_compatibilidade(adotante_id: int, db: Session = Depends(get_db)):
    """
    Cenário 1: calcula a nota (0 a 100) de cada animal disponível que passou nos filtros.
    Cenário 2: ordena do mais para o menos compatível; destaque = nota igual ou maior que 75.
    Cenário 3: sem perfil completo, bloqueia o cálculo (409) e indica os campos que faltam.
    """
    obter_adotante_ou_404(adotante_id, db)
    perfil = db.query(models.PerfilAdotante).filter(models.PerfilAdotante.adotante_id == adotante_id).first()
    faltando = CAMPOS_PERFIL if perfil is None else [c for c in CAMPOS_PERFIL if getattr(perfil, c) is None]
    if faltando:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "mensagem": "Complete o seu perfil de adoção para ver os animais compatíveis.",
                "campos_faltando": faltando,
            },
        )
    criterios = compatibilidade.garantir_criterios(db)
    animais = db.query(models.Animal).order_by(models.Animal.id).all()
    resultado, eliminados = compatibilidade.calcular(perfil, animais, criterios)
    return {"adotante_id": adotante_id, "animais": resultado, "eliminados": eliminados}


# =====================================================================
# HU05 - Solicitação de adoção
# =====================================================================
def montar_solicitacao(s: models.SolicitacaoAdocao, db: Session) -> dict:
    animal = db.get(models.Animal, s.animal_id)
    adotante = db.get(models.Adotante, s.adotante_id)
    return {
        "id": s.id,
        "adotante_id": s.adotante_id,
        "animal_id": s.animal_id,
        "status": s.status,
        "criado_em": s.criado_em,
        "animal_nome": animal.nome if animal else None,
        "animal_foto_url": animal.foto_url if animal else None,
        "adotante_nome": adotante.nome_completo if adotante else None,
    }


def obter_solicitacao_ou_404(solicitacao_id: int, db: Session) -> models.SolicitacaoAdocao:
    s = db.get(models.SolicitacaoAdocao, solicitacao_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    return s


@app.post(
    "/solicitacoes",
    response_model=schemas.SolicitacaoResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Solicitação de adoção"],
)
def solicitar_adocao(
    dados: schemas.SolicitacaoCreate,
    adotante: models.Adotante = Depends(adotante_logado),
    db: Session = Depends(get_db),
):
    """
    Cenário 1: registra a solicitação ligando o adotante logado ao animal.
    Cenário 2: devolve 201 e a solicitação fica "pendente" para acompanhamento.
    Cenário 3: animal indisponível -> 409. O animal é reservado numa única operação
    (só muda se ainda estiver disponível), então dois pedidos ao mesmo tempo não passam (RISK06).
    """
    if dados.adotante_id != adotante.id:
        raise HTTPException(status_code=403, detail="A solicitação deve ser feita pelo adotante logado.")
    if db.get(models.Animal, dados.animal_id) is None:
        raise HTTPException(status_code=404, detail="Animal não encontrado.")

    reservados = (
        db.query(models.Animal)
        .filter(models.Animal.id == dados.animal_id, models.Animal.disponivel.is_(True))
        .update({models.Animal.disponivel: False}, synchronize_session=False)
    )
    if reservados == 0:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este animal não está mais disponível para adoção.",
        )
    solicitacao = models.SolicitacaoAdocao(adotante_id=adotante.id, animal_id=dados.animal_id, status="pendente")
    db.add(solicitacao)
    db.commit()
    db.refresh(solicitacao)
    return montar_solicitacao(solicitacao, db)


@app.get("/solicitacoes", response_model=list[schemas.SolicitacaoResponse], tags=["Solicitação de adoção"])
def listar_solicitacoes(
    adotante_id: int | None = None, status_filtro: str | None = Query(default=None, alias="status"), db: Session = Depends(get_db)
):
    """Lista as solicitações (do adotante, com ?adotante_id=, ou todas, para o responsável)."""
    consulta = db.query(models.SolicitacaoAdocao)
    if adotante_id is not None:
        consulta = consulta.filter(models.SolicitacaoAdocao.adotante_id == adotante_id)
    if status_filtro:
        consulta = consulta.filter(models.SolicitacaoAdocao.status == status_filtro)
    return [montar_solicitacao(s, db) for s in consulta.order_by(models.SolicitacaoAdocao.id.desc()).all()]


@app.patch(
    "/solicitacoes/{solicitacao_id}",
    response_model=schemas.SolicitacaoResponse,
    tags=["Solicitação de adoção"],
)
def decidir_solicitacao(solicitacao_id: int, dados: schemas.SolicitacaoStatus, db: Session = Depends(get_db)):
    """O responsável aprova (adoção concluída) ou recusa (o animal volta a ficar disponível)."""
    s = obter_solicitacao_ou_404(solicitacao_id, db)
    if s.status != "pendente":
        raise HTTPException(status_code=409, detail="Esta solicitação já foi decidida.")
    s.status = dados.status
    if dados.status == "recusada":
        animal = db.get(models.Animal, s.animal_id)
        if animal:
            animal.disponivel = True
    db.commit()
    db.refresh(s)
    return montar_solicitacao(s, db)


# =====================================================================
# HU06 - Acompanhamento pós-adoção
# =====================================================================
PASTA_FOTOS = Path(os.getenv("FOTOS_DIR", Path(__file__).resolve().parent / "fotos_acompanhamento"))
TAMANHO_MAXIMO_FOTO = 5 * 1024 * 1024  # 5 MB (RISK07)


def tipo_da_foto(conteudo: bytes) -> str | None:
    """Identifica o formato pelo conteúdo do arquivo, não pelo nome."""
    if conteudo.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        return ".webp"
    return None


def montar_acompanhamento(a: models.Acompanhamento) -> dict:
    return {
        "id": a.id,
        "solicitacao_id": a.solicitacao_id,
        "descricao": a.descricao,
        "foto_url": f"/fotos/{a.foto_arquivo}",
        "criado_em": a.criado_em,
    }


@app.post(
    "/solicitacoes/{solicitacao_id}/acompanhamentos",
    response_model=schemas.AcompanhamentoResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Acompanhamento pós-adoção"],
)
async def registrar_acompanhamento(
    solicitacao_id: int,
    descricao: str = Form(default=""),
    foto: UploadFile | None = File(default=None),
    adotante: models.Adotante = Depends(adotante_logado),
    db: Session = Depends(get_db),
):
    """
    Cenário 1: adoção concluída (aprovada) -> grava texto e foto no histórico daquela adoção.
    Cenário 3: sem foto ou sem texto -> 422 indicando o que falta. Foto só JPG, PNG ou WEBP até 5 MB.
    """
    s = obter_solicitacao_ou_404(solicitacao_id, db)
    if s.adotante_id != adotante.id:
        raise HTTPException(status_code=403, detail="Só o adotante desta adoção pode enviar atualizações.")
    if s.status != "aprovada":
        raise HTTPException(status_code=409, detail="O acompanhamento só fica disponível depois que a adoção é concluída.")

    erros = []
    descricao = descricao.strip()
    if not descricao:
        erros.append({"campo": "descricao", "mensagem": "Conte como está a adaptação do animal."})
    conteudo = await foto.read(TAMANHO_MAXIMO_FOTO + 1) if foto is not None else b""
    extensao = None
    if not conteudo:
        erros.append({"campo": "foto", "mensagem": "Envie uma foto do animal."})
    elif len(conteudo) > TAMANHO_MAXIMO_FOTO:
        erros.append({"campo": "foto", "mensagem": "A foto deve ter no máximo 5 MB."})
    else:
        extensao = tipo_da_foto(conteudo)
        if extensao is None:
            erros.append({"campo": "foto", "mensagem": "Envie a foto em JPG, PNG ou WEBP."})
    if erros:
        raise HTTPException(status_code=422, detail=erros)

    PASTA_FOTOS.mkdir(parents=True, exist_ok=True)
    nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
    (PASTA_FOTOS / nome_arquivo).write_bytes(conteudo)

    registro = models.Acompanhamento(solicitacao_id=s.id, descricao=descricao, foto_arquivo=nome_arquivo)
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return montar_acompanhamento(registro)


@app.get(
    "/solicitacoes/{solicitacao_id}/acompanhamentos",
    response_model=list[schemas.AcompanhamentoResponse],
    tags=["Acompanhamento pós-adoção"],
)
def listar_acompanhamentos(solicitacao_id: int, db: Session = Depends(get_db)):
    """Cenário 2: histórico da adoção, da atualização mais recente para a mais antiga."""
    obter_solicitacao_ou_404(solicitacao_id, db)
    registros = (
        db.query(models.Acompanhamento)
        .filter(models.Acompanhamento.solicitacao_id == solicitacao_id)
        .order_by(models.Acompanhamento.id.desc())
        .all()
    )
    return [montar_acompanhamento(a) for a in registros]


@app.get("/fotos/{arquivo}", include_in_schema=False)
def servir_foto(arquivo: str):
    caminho = (PASTA_FOTOS / arquivo).resolve()
    if caminho.parent != PASTA_FOTOS.resolve() or not caminho.is_file():
        raise HTTPException(status_code=404, detail="Foto não encontrada.")
    return FileResponse(caminho)


async def salvar_foto(foto: UploadFile | None) -> str:
    """Valida (JPG, PNG ou WEBP, até 5 MB) e grava a foto; devolve o nome do arquivo."""
    conteudo = await foto.read(TAMANHO_MAXIMO_FOTO + 1) if foto is not None else b""
    if not conteudo:
        raise HTTPException(status_code=422, detail=[{"campo": "foto", "mensagem": "Envie uma foto do animal."}])
    if len(conteudo) > TAMANHO_MAXIMO_FOTO:
        raise HTTPException(status_code=422, detail=[{"campo": "foto", "mensagem": "A foto deve ter no máximo 5 MB."}])
    extensao = tipo_da_foto(conteudo)
    if extensao is None:
        raise HTTPException(status_code=422, detail=[{"campo": "foto", "mensagem": "Envie a foto em JPG, PNG ou WEBP."}])
    PASTA_FOTOS.mkdir(parents=True, exist_ok=True)
    nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
    (PASTA_FOTOS / nome_arquivo).write_bytes(conteudo)
    return nome_arquivo


@app.post("/animais/{animal_id}/foto", response_model=schemas.AnimalResponse, tags=["Animais"])
async def enviar_foto_animal(
    animal_id: int, foto: UploadFile | None = File(default=None), db: Session = Depends(get_db)
):
    """Foto do animal (opcional), mostrada nos cards. Mesmas regras de formato e tamanho da HU06."""
    animal = db.get(models.Animal, animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal não encontrado.")
    animal.foto_arquivo = await salvar_foto(foto)
    db.commit()
    db.refresh(animal)
    return animal


# Telas servidas pela própria API (usado no Codespaces, onde só a porta 8000 é aberta).
# Só entrega .html, .js e .css da pasta frontend; fica por último para não encobrir as rotas da API.
PASTA_TELAS = Path(__file__).resolve().parent.parent / "frontend"
EXTENSOES_TELAS = {".html", ".js", ".css"}


@app.get("/{arquivo:path}", include_in_schema=False)
def servir_tela(arquivo: str):
    caminho = (PASTA_TELAS / arquivo).resolve()
    dentro_da_pasta = PASTA_TELAS.resolve() in caminho.parents
    if not dentro_da_pasta or caminho.suffix not in EXTENSOES_TELAS or not caminho.is_file():
        raise HTTPException(status_code=404, detail="Página não encontrada.")
    return FileResponse(caminho)
