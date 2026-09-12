"""
Schemas Pydantic: validação de entrada (Create) e formato de saída (Response).
"""
import re
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict


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
        return v

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) != 2:
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
