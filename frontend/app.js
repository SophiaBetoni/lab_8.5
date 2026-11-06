// Front-end (cliente): só conversa com o back-end pela API, sem acesso direto a dados.
const API = window.API_URL;
let token = localStorage.getItem("token");
let statusFiltro = "";

const $ = (id) => document.getElementById(id);
const ROTULOS = { lido: "Lido", lendo: "Lendo", quero_ler: "Quero ler" };

function mostrarMensagem(texto) {
  $("mensagem").textContent = texto || "";
}

async function api(caminho, { method = "GET", corpo } = {}) {
  const resposta = await fetch(API + caminho, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: "Bearer " + token } : {}),
    },
    body: corpo ? JSON.stringify(corpo) : undefined,
  });
  if (resposta.status === 204) return null;
  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    if (resposta.status === 401 && token) sair();
    const detalhe = Array.isArray(dados.detail) ? "Dados inválidos" : dados.detail;
    throw new Error(detalhe || "Erro na requisição");
  }
  return dados;
}

// ---------- Autenticação ----------
async function autenticar(rota) {
  mostrarMensagem("");
  try {
    const dados = await api(rota, {
      method: "POST",
      corpo: { username: $("login-usuario").value.trim(), password: $("login-senha").value },
    });
    token = dados.token;
    localStorage.setItem("token", token);
    $("login-senha").value = "";
    await iniciarApp();
  } catch (erro) {
    mostrarMensagem(erro.message);
  }
}

function sair() {
  token = null;
  localStorage.removeItem("token");
  $("tela-app").hidden = true;
  $("barra-usuario").hidden = true;
  $("tela-login").hidden = false;
}

// ---------- Renderização ----------
function estrelas(nota) {
  return nota ? "★".repeat(nota) + "☆".repeat(5 - nota) : "sem nota";
}

async function carregarPerfil() {
  const perfil = await api("/perfil");
  $("nome-usuario").textContent = perfil.username;
  $("resumo-perfil").textContent =
    `${perfil.total_lidos} lidos · ${perfil.total_lendo} lendo · ${perfil.total_quero_ler} quero ler`;
  const lista = $("lista-favoritos");
  lista.innerHTML = "";
  if (!perfil.favoritos.length) {
    lista.innerHTML = "<li class='autor'>Marque até 3 livros com ♥</li>";
  }
  perfil.favoritos.forEach((f) => {
    const li = document.createElement("li");
    li.textContent = `${f.livro.titulo} — ${f.livro.autor}`;
    lista.appendChild(li);
  });
}

async function carregarLista() {
  const leituras = await api("/minha-lista" + (statusFiltro ? `?status=${statusFiltro}` : ""));
  const ul = $("lista-leituras");
  ul.innerHTML = "";
  if (!leituras.length) ul.innerHTML = "<li class='autor'>Nenhum livro aqui ainda.</li>";
  leituras.forEach((l) => {
    const li = document.createElement("li");
    li.className = "leitura";

    const info = document.createElement("div");
    const titulo = document.createElement("strong");
    titulo.textContent = l.livro.titulo;
    const autor = document.createElement("div");
    autor.className = "autor";
    autor.textContent = `${l.livro.autor} · ${ROTULOS[l.status]} · ${estrelas(l.nota)}`;
    info.append(titulo, autor);

    const acoes = document.createElement("div");
    acoes.className = "acoes";

    const seletor = document.createElement("select");
    Object.entries(ROTULOS).forEach(([valor, rotulo]) => {
      const op = new Option(rotulo, valor, false, valor === l.status);
      seletor.add(op);
    });
    seletor.onchange = () => atualizar(l.id, { status: seletor.value });

    const nota = document.createElement("select");
    nota.add(new Option("nota", ""));
    for (let n = 1; n <= 5; n++) nota.add(new Option(String(n), String(n), false, n === l.nota));
    nota.onchange = () => nota.value && atualizar(l.id, { nota: Number(nota.value) });

    const fav = document.createElement("button");
    fav.className = "secundario";
    fav.textContent = l.favorito ? "♥" : "♡";
    fav.onclick = () => atualizar(l.id, { favorito: !l.favorito });

    const remover = document.createElement("button");
    remover.className = "secundario";
    remover.textContent = "Remover";
    remover.onclick = async () => {
      try {
        await api(`/minha-lista/${l.id}`, { method: "DELETE" });
        await recarregar();
      } catch (e) {
        mostrarMensagem(e.message);
      }
    };

    acoes.append(seletor, nota, fav, remover);
    li.append(info, acoes);
    ul.appendChild(li);
  });
}

async function recarregar() {
  mostrarMensagem("");
  await Promise.all([carregarPerfil(), carregarLista()]);
}

async function atualizar(id, mudancas) {
  try {
    await api(`/minha-lista/${id}`, { method: "PATCH", corpo: mudancas });
    await recarregar();
  } catch (erro) {
    mostrarMensagem(erro.message);
    await carregarLista();
  }
}

async function iniciarApp() {
  try {
    await recarregar();
    $("tela-login").hidden = true;
    $("tela-app").hidden = false;
    $("barra-usuario").hidden = false;
  } catch (erro) {
    mostrarMensagem("Não foi possível falar com o servidor: " + erro.message);
  }
}

// ---------- Eventos ----------
$("form-login").addEventListener("submit", (e) => {
  e.preventDefault();
  autenticar("/auth/login");
});
$("btn-registrar").addEventListener("click", () => {
  if ($("form-login").reportValidity()) autenticar("/auth/registro");
});
$("btn-sair").addEventListener("click", sair);

$("form-livro").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const livro = await api("/livros", {
      method: "POST",
      corpo: { titulo: $("livro-titulo").value.trim(), autor: $("livro-autor").value.trim() },
    });
    await api("/minha-lista", {
      method: "POST",
      corpo: { livro_id: livro.id, status: $("livro-status").value },
    });
    e.target.reset();
    await recarregar();
  } catch (erro) {
    mostrarMensagem(erro.message);
  }
});

$("abas").addEventListener("click", async (e) => {
  if (e.target.tagName !== "BUTTON") return;
  statusFiltro = e.target.dataset.status;
  document.querySelectorAll("#abas button").forEach((b) => b.classList.toggle("ativa", b === e.target));
  await carregarLista();
});

if (token) iniciarApp();
