"""
MatchPet API - HU01: Cadastro do Adotante
Código base: criação de conta do adotante com validações essenciais.
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from database import engine, get_db, Base
import models
import schemas

# Cria as tabelas (em produção, prefira migrations com Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MatchPet API", version="0.1.0")

# CORS liberado para o front-end local (ajustar em produção)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@app.get("/")
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
    senha_hash = pwd_context.hash(dados.senha)

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
