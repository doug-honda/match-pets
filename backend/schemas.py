"""
Schemas Pydantic: validação de entrada (Create) e formato de saída (Response).
"""
import re
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


CAMPOS_TEXTO_OBRIGATORIOS = ("nome_completo", "logradouro", "numero", "bairro", "cidade")


class AdotanteCreate(BaseModel):
    nome_completo: str
    cpf: str
    email: EmailStr
    telefone: str
    data_nascimento: date
    senha: str

    cep: str
    logradouro: str
    numero: str
    complemento: str | None = None
    bairro: str
    cidade: str
    estado: str

    @field_validator(*CAMPOS_TEXTO_OBRIGATORIOS)
    @classmethod
    def validar_preenchido(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Campo obrigatório")
        return v

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        cpf_limpo = re.sub(r"\D", "", v)
        if len(cpf_limpo) != 11:
            raise ValueError("CPF deve conter 11 dígitos")
        return cpf_limpo

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, v: str) -> str:
        telefone_limpo = re.sub(r"\D", "", v)
        if len(telefone_limpo) < 10 or len(telefone_limpo) > 11:
            raise ValueError("Telefone inválido")
        return telefone_limpo

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter ao menos 8 caracteres")
        # Limite do algoritmo bcrypt: 72 bytes
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Senha deve ter no máximo 72 caracteres")
        return v

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", v):
            raise ValueError("Estado deve ser a sigla (ex: SP)")
        return v

    @field_validator("cep")
    @classmethod
    def validar_cep(cls, v: str) -> str:
        cep_limpo = re.sub(r"\D", "", v)
        if len(cep_limpo) != 8:
            raise ValueError("CEP deve conter 8 dígitos")
        return f"{cep_limpo[:5]}-{cep_limpo[5:]}"


class AdotanteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_completo: str
    cpf: str
    email: str
    telefone: str
    data_nascimento: date
    cep: str
    logradouro: str
    numero: str
    complemento: str | None
    bairro: str
    cidade: str
    estado: str
    criado_em: datetime


class AnimalCreate(BaseModel):
    """Cadastro do animal (HU02). Inclui os campos usados no cálculo de compatibilidade (HU04)."""
    nome: str
    especie: Literal["cao", "gato"]
    porte: Literal["pequeno", "medio", "grande"]
    idade_anos: int = Field(ge=0, le=30)
    nivel_energia: Literal["baixo", "medio", "alto"]
    convive_criancas: bool
    convive_outros_animais: bool
    tolerancia_sozinho: Literal["baixa", "media", "alta"]
    exige_experiencia: bool
    disponivel: bool
    descricao: str | None = None

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Campo obrigatório")
        return v

    @field_validator("descricao")
    @classmethod
    def limpar_descricao(cls, v: str | None) -> str | None:
        v = (v or "").strip()
        return v or None


class AnimalResponse(AnimalCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: datetime
    foto_url: str | None = None


class AnimalDisponibilidade(BaseModel):
    disponivel: bool


class PerfilAdotanteDados(BaseModel):
    """Perfil de adoção (HU03). Todos os campos são obrigatórios (cenário 2)."""
    tipo_moradia: Literal["apartamento", "casa_sem_quintal", "casa_com_quintal"]
    tem_criancas: bool
    tem_outros_animais: bool
    nivel_atividade: Literal["baixo", "medio", "alto"]
    horas_sozinho: Literal["ate_4", "4_a_8", "mais_de_8"]
    ja_teve_pet: bool
    especie_preferida: Literal["cao", "gato", "indiferente"]
    porte_preferido: Literal["pequeno", "medio", "grande", "indiferente"]


class PerfilAdotanteResponse(PerfilAdotanteDados):
    model_config = ConfigDict(from_attributes=True)

    adotante_id: int
    criado_em: datetime
    atualizado_em: datetime


# ---------------------------------------------------------------- Sprint 2

class LoginDados(BaseModel):
    email: EmailStr
    senha: str


class LoginResponse(BaseModel):
    adotante_id: int
    nome_completo: str
    token: str


class CriterioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nome: str
    tipo: str
    peso: int
    descricao: str


class AnimalCompativel(BaseModel):
    """Um animal que passou pelos filtros, com a nota (0 a 100) e o detalhe por critério."""
    animal: AnimalResponse
    nota: int
    faixa: Literal["alta", "media", "baixa"]
    destaque: bool
    pontos_por_criterio: dict[str, int]


class CompatibilidadeResponse(BaseModel):
    adotante_id: int
    animais: list[AnimalCompativel]
    eliminados: int


class SolicitacaoCreate(BaseModel):
    adotante_id: int
    animal_id: int


class SolicitacaoStatus(BaseModel):
    status: Literal["aprovada", "recusada"]


class SolicitacaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    adotante_id: int
    animal_id: int
    status: str
    criado_em: datetime
    animal_nome: str | None = None
    animal_foto_url: str | None = None
    adotante_nome: str | None = None


class AcompanhamentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    solicitacao_id: int
    descricao: str
    foto_url: str
    criado_em: datetime
