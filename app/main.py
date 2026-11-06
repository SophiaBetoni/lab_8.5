import hashlib
import os
import secrets
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Leitor API", description="Back-end do MVP de controle de leituras")

# CORS: no deploy, defina ALLOWED_ORIGINS com a URL do front-end (separadas por vírgula).
origens = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens,
    allow_methods=["*"],
    allow_headers=["*"],
)


def gerar_hash(senha: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 100_000).hex()


def usuario_atual(
    authorization: str = Header(default=""), db: Session = Depends(get_db)
) -> models.User:
    token = authorization.removeprefix("Bearer ").strip()
    usuario = (
        db.query(models.User).filter(models.User.token == token).first() if token else None
    )
    if not usuario:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return usuario


@app.get("/")
def raiz():
    return {"status": "ok", "docs": "/docs"}


# ---------- Autenticação ----------
@app.post("/auth/registro", response_model=schemas.TokenOut, status_code=201)
def registro(dados: schemas.Credenciais, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == dados.username).first():
        raise HTTPException(status_code=409, detail="Nome de usuário já existe")
    salt = secrets.token_hex(8)
    usuario = models.User(
        username=dados.username,
        salt=salt,
        password_hash=gerar_hash(dados.password, salt),
        token=secrets.token_hex(24),
    )
    db.add(usuario)
    db.commit()
    return schemas.TokenOut(token=usuario.token, username=usuario.username)


@app.post("/auth/login", response_model=schemas.TokenOut)
def login(dados: schemas.Credenciais, db: Session = Depends(get_db)):
    usuario = db.query(models.User).filter(models.User.username == dados.username).first()
    if not usuario or gerar_hash(dados.password, usuario.salt) != usuario.password_hash:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    if not usuario.token:
        usuario.token = secrets.token_hex(24)
        db.commit()
    return schemas.TokenOut(token=usuario.token, username=usuario.username)


# ---------- Catálogo de livros ----------
@app.get("/livros", response_model=List[schemas.LivroOut])
def listar_livros(q: Optional[str] = None, db: Session = Depends(get_db)):
    consulta = db.query(models.Book)
    if q:
        padrao = f"%{q}%"
        consulta = consulta.filter(
            models.Book.titulo.ilike(padrao) | models.Book.autor.ilike(padrao)
        )
    return consulta.order_by(models.Book.titulo).limit(100).all()


@app.post("/livros", response_model=schemas.LivroOut, status_code=201)
def criar_livro(
    dados: schemas.LivroIn,
    db: Session = Depends(get_db),
    _: models.User = Depends(usuario_atual),
):
    livro = models.Book(**dados.model_dump())
    db.add(livro)
    db.commit()
    db.refresh(livro)
    return livro


# ---------- Lista de leituras do usuário ----------
def _total_favoritos(db: Session, usuario_id: int) -> int:
    return (
        db.query(models.UserBook)
        .filter(models.UserBook.usuario_id == usuario_id, models.UserBook.favorito.is_(True))
        .count()
    )


@app.get("/minha-lista", response_model=List[schemas.LeituraOut])
def minha_lista(
    status: Optional[schemas.Status] = None,
    db: Session = Depends(get_db),
    usuario: models.User = Depends(usuario_atual),
):
    consulta = db.query(models.UserBook).filter(models.UserBook.usuario_id == usuario.id)
    if status:
        consulta = consulta.filter(models.UserBook.status == status)
    return consulta.order_by(models.UserBook.id.desc()).all()


@app.post("/minha-lista", response_model=schemas.LeituraOut, status_code=201)
def adicionar_leitura(
    dados: schemas.LeituraIn,
    db: Session = Depends(get_db),
    usuario: models.User = Depends(usuario_atual),
):
    if not db.get(models.Book, dados.livro_id):
        raise HTTPException(status_code=404, detail="Livro não encontrado")
    ja_existe = (
        db.query(models.UserBook)
        .filter(
            models.UserBook.usuario_id == usuario.id,
            models.UserBook.livro_id == dados.livro_id,
        )
        .first()
    )
    if ja_existe:
        raise HTTPException(status_code=409, detail="Livro já está na sua lista")
    if dados.favorito and _total_favoritos(db, usuario.id) >= 3:
        raise HTTPException(status_code=400, detail="Você já tem 3 favoritos")
    leitura = models.UserBook(usuario_id=usuario.id, **dados.model_dump())
    db.add(leitura)
    db.commit()
    db.refresh(leitura)
    return leitura


@app.patch("/minha-lista/{leitura_id}", response_model=schemas.LeituraOut)
def atualizar_leitura(
    leitura_id: int,
    dados: schemas.LeituraUpdate,
    db: Session = Depends(get_db),
    usuario: models.User = Depends(usuario_atual),
):
    leitura = db.get(models.UserBook, leitura_id)
    if not leitura or leitura.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Leitura não encontrada")
    mudancas = dados.model_dump(exclude_unset=True)
    if mudancas.get("favorito") and not leitura.favorito:
        if _total_favoritos(db, usuario.id) >= 3:
            raise HTTPException(status_code=400, detail="Você já tem 3 favoritos")
    for campo, valor in mudancas.items():
        setattr(leitura, campo, valor)
    db.commit()
    db.refresh(leitura)
    return leitura


@app.delete("/minha-lista/{leitura_id}", status_code=204)
def remover_leitura(
    leitura_id: int,
    db: Session = Depends(get_db),
    usuario: models.User = Depends(usuario_atual),
):
    leitura = db.get(models.UserBook, leitura_id)
    if not leitura or leitura.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Leitura não encontrada")
    db.delete(leitura)
    db.commit()


# ---------- Perfil ----------
@app.get("/perfil", response_model=schemas.PerfilOut)
def perfil(
    db: Session = Depends(get_db), usuario: models.User = Depends(usuario_atual)
):
    leituras = db.query(models.UserBook).filter(models.UserBook.usuario_id == usuario.id).all()
    return schemas.PerfilOut(
        username=usuario.username,
        total_lidos=sum(1 for l in leituras if l.status == "lido"),
        total_lendo=sum(1 for l in leituras if l.status == "lendo"),
        total_quero_ler=sum(1 for l in leituras if l.status == "quero_ler"),
        favoritos=[l for l in leituras if l.favorito][:3],
    )
