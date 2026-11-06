from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    username = Column(String(30), unique=True, nullable=False)
    salt = Column(String(32), nullable=False)
    password_hash = Column(String(128), nullable=False)
    token = Column(String(64), index=True)


class Book(Base):
    __tablename__ = "livros"

    id = Column(Integer, primary_key=True)
    titulo = Column(String(200), nullable=False)
    autor = Column(String(120), nullable=False)


class UserBook(Base):
    """Livro na lista de um usuário: lido, lendo ou quero_ler."""

    __tablename__ = "leituras"
    __table_args__ = (UniqueConstraint("usuario_id", "livro_id"),)

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    livro_id = Column(Integer, ForeignKey("livros.id"), nullable=False)
    status = Column(String(20), nullable=False)
    nota = Column(Integer)
    favorito = Column(Boolean, default=False, nullable=False)

    livro = relationship("Book")
