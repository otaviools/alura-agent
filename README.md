# Docsy

O Docsy recebe um arquivo PDF e abre um chat sobre o conteúdo dele. Cada
resposta cita a página de origem no formato `(página N)`.

Projeto pessoal de Otávio Santos.

## O que faz

O Docsy extrai o texto do PDF página a página. Um agente construído com
LangChain busca os trechos relevantes, lê as páginas necessárias e responde em
português citando a origem no formato `(página N)`.

A aplicação não grava dados em disco nem em banco. O documento e a conversa
ficam na memória do servidor e são descartados ao trocar de arquivo, ao remover
o documento, após 60 minutos de inatividade ou quando o servidor reinicia.

## Stack

Back-end:

- Python 3.14.0
- Flask 3.1.3 — servidor HTTP e rotas
- LangChain 1.3.16 + langchain-google-genai 4.3.5 — agente e ferramentas
- pdfplumber 0.11.10 — extração de texto do PDF
- rank-bm25 0.2.2 — busca por palavras dentro do documento
- Flask-Limiter 4.1.1 — limite de requisições por origem

Front-end:

- Node 24.15.0
- Nuxt 4.5.2 (Vue 3 sobre Nitro)
- Nuxt UI 4.10.0 — componentes de interface: barra lateral, chat e upload
- Tailwind CSS 4.3.3
- @iconify-json/lucide — ícones

Modelo de IA: Google Gemini (`gemini-flash-lite-latest` por padrão).

## Como rodar

Pré-requisitos: Python 3.14, Node 24 e uma chave da API do Google Gemini
([aistudio.google.com/apikey](https://aistudio.google.com/apikey)).

Se o projeto estiver em uma pasta com caminho muito longo, a instalação das
dependências Python pode falhar com `OSError: [Errno 2] No such file or
directory`. É o limite de 260 caracteres do Windows. Mova o projeto para uma
pasta com caminho mais curto ou habilite o suporte a caminhos longos.

### 1. Back-end

Crie o ambiente virtual:

```bash
cd backend && python -m venv .venv
```

Instale as dependências:

```bash
cd backend && .venv/Scripts/python.exe -m pip install -r requirements.txt
```

Copie o arquivo de exemplo:

```bash
cp backend/.env.example backend/.env
```

Edite `backend/.env` e substitua o valor de `GOOGLE_API_KEY` pela sua chave.
Sem a chave, a aplicação sobe, aceita o PDF e mostra os metadados, mas o chat
responde que o serviço de IA não está configurado.

Suba o servidor:

```bash
cd backend && .venv/Scripts/python.exe run.py
```

A API fica em `http://127.0.0.1:5000`. Confira com
`curl http://127.0.0.1:5000/api/saude`.

### 2. Front-end

Em outro terminal, instale as dependências:

```bash
cd frontend && npm install
```

Suba o servidor de desenvolvimento:

```bash
cd frontend && npm run dev
```

Abra `http://localhost:3000`. O Nuxt repassa ao back-end tudo que começa com
`/api`, então o navegador usa uma origem só.

### 3. Testes

```bash
cd backend && .venv/Scripts/python.exe -m pytest tests -q
```

Os 18 testes rodam sem chamar a API do Gemini. O agente é exercitado com um
modelo falso do próprio LangChain.

## Endpoints

Todas as rotas exigem o cabeçalho `X-Sessao`, exceto `/api/saude` e a criação da
sessão. As rotas que alteram estado exigem também `X-Token-Protecao`.

| O que faz | Método e rota | Request | Response | Erros |
|---|---|---|---|---|
| Abre sessão | `POST /api/sessoes` | sem corpo | `201` `{sessaoId, tokenProtecao, expiraEmMinutos}` | `429` limite de requisições |
| Envia um PDF | `POST /api/documentos` | `multipart/form-data`, campo `arquivo` | `201` `{nomeArquivo, tamanhoBytes, totalPaginas, paginasComTexto, totalCaracteres, possuiTexto, criadoEm, aviso?}` | `400` inválido, não-PDF, com senha ou acima de 300 páginas; `403` token ausente; `404` sessão expirada; `413` acima de 20 MB; `429` limite |
| Consulta o documento | `GET /api/documentos` | — | `200` metadados, ou `{"documento": null}` | `404` sessão expirada |
| Pergunta | `POST /api/mensagens` | `{"pergunta": "texto"}` | `200` `text/event-stream`, uma linha `data:` por evento | `400` pergunta vazia ou acima de 2.000 caracteres; `403` token ausente; `404` sessão expirada ou sem documento; `429` limite |
| Lista o histórico | `GET /api/mensagens` | — | `200` `{mensagens: [{autor, texto, criadoEm}]}` | `404` sessão expirada |
| Remove o documento | `DELETE /api/documentos` | — | `200` `{removido: true}` | `403` token ausente; `404` sessão expirada |
| Verifica o serviço | `GET /api/saude` | — | `200` `{status, agenteConfigurado, modelo, sessoesAtivas, limites}` | — |

### Eventos do streaming

O corpo de `POST /api/mensagens` traz um JSON por evento:

| Evento | Formato | Significado |
|---|---|---|
| `ferramenta` | `{"tipo":"ferramenta","nome":"buscar_trechos"}` | O agente está consultando o documento |
| `texto` | `{"tipo":"texto","conteudo":"..."}` | Pedaço da resposta, na ordem em que é gerada |
| `fim` | `{"tipo":"fim","resposta":"..."}` | Resposta completa; o histórico é gravado só aqui |
| `erro` | `{"tipo":"erro","mensagem":"..."}` | Falha tratada, com texto pronto para exibição |

### Ferramentas do agente

| Ferramenta | O que faz |
|---|---|
| `buscar_trechos` | Busca BM25 nos trechos do documento e devolve os mais relevantes com o número da página |
| `ler_pagina` | Devolve o texto completo de uma página |
| `informacoes_documento` | Devolve nome, número de páginas e o início do documento |

## Estruturas em memória

Definidas em `backend/app/models/documento.py`.

| Estrutura | Finalidade | Campos |
|---|---|---|
| `Sessao` | Une documento e conversa a um usuário anônimo | `identificador`, `token_protecao`, `documento`, `mensagens`, `criada_em`, `ultimo_acesso` |
| `Documento` | PDF carregado e seu texto | `nome_arquivo`, `tamanho_bytes`, `total_paginas`, `paginas`, `trechos`, `criado_em` |
| `Pagina` | Texto de uma página | `numero`, `texto` |
| `Trecho` | Bloco indexável de uma página, usado na busca | `pagina`, `ordem`, `texto` |
| `Mensagem` | Uma fala da conversa | `autor`, `texto`, `criado_em` |

## Estrutura de pastas

```
docsy/
├── backend/                     # Python + Flask + LangChain
│   ├── app/
│   │   ├── __init__.py          # fábrica da aplicação e tratamento de erros
│   │   ├── config.py            # configuração por variável de ambiente
│   │   ├── routes/              # rotas finas
│   │   ├── services/            # regra de negócio (PDF, busca, agente, sessão)
│   │   ├── middleware/          # segurança e limite de requisições
│   │   ├── models/              # estruturas em memória
│   │   └── utils/               # erros de domínio e log
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
├── frontend/                    # Nuxt 4
│   ├── app/
│   │   ├── components/          # componente próprio (painel do documento)
│   │   ├── composables/         # estado compartilhado
│   │   ├── services/            # única camada que fala com a API
│   │   ├── pages/               # telas
│   │   ├── assets/              # CSS e fontes
│   │   ├── app.config.ts        # tema do Nuxt UI
│   │   └── app.vue
│   ├── public/                  # favicon
│   ├── nuxt.config.ts
│   └── package.json
├── PLANEJAMENTO.md              # decisões técnicas e limitações
└── README.md
```

## Limitações

- O conteúdo do documento é enviado à API do Google Gemini. Não use com
  documento que você não possa compartilhar com um serviço de terceiros.
- Não há OCR. PDF escaneado como imagem é aceito, mas não tem texto para ler; a
  interface avisa.
- Não há login. Para publicar na internet, é preciso adicionar autenticação.
- O estado em memória e o limite de requisições assumem uma instância só.

As decisões técnicas e as ideias futuras estão em [PLANEJAMENTO.md](PLANEJAMENTO.md).

## Licenças de terceiros

- Dependências Python e Node: MIT, BSD ou Apache-2.0. Ver `requirements.txt` e
  `package.json`.
- Fontes Titillium Web e Fira Sans: SIL Open Font License 1.1.
- Ícones Lucide: ISC.
- Nuxt UI: MIT.
