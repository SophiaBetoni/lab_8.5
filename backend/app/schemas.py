from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["lido", "lendo", "quero_ler"]


class Credenciais(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=4, max_length=100)


class TokenOut(BaseModel):
    token: str
    username: str


class LivroIn(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    autor: str = Field(min_length=1, max_length=120)


class LivroOut(LivroIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class LeituraIn(BaseModel):
    livro_id: int
    status: Status
    nota: Optional[int] = Field(default=None, ge=1, le=5)
    favorito: bool = False


class LeituraUpdate(BaseModel):
    status: Optional[Status] = None
    nota: Optional[int] = Field(default=None, ge=1, le=5)
    favorito: Optional[bool] = None


class LeituraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: Status
    nota: Optional[int]
    favorito: bool
    livro: LivroOut


class PerfilOut(BaseModel):
    username: str
    total_lidos: int
    total_lendo: int
    total_quero_ler: int
    favoritos: List[LeituraOut]
