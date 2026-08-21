# Planejamento — Docsy

Projeto pessoal. Documento de decisões: o que a aplicação faz, o que ficou de
fora e por quê.

## Problema

Ler um PDF longo para achar uma informação específica consome tempo. Contrato,
manual, apostila, edital, artigo — a pessoa sabe o que quer saber, mas precisa
varrer dezenas de páginas para encontrar.

O Docsy recebe um PDF e abre um chat sobre ele. A pergunta é feita em linguagem
natural e a resposta vem com a indicação da página de origem, para conferência
na fonte.

## Escopo

### Dentro

- Envio de um PDF por vez, com validação de tipo, tamanho e número de páginas.
- Extração do texto página a página.
- Chat com um agente que busca no documento, lê páginas e responde citando a
  origem.
- Histórico da conversa dentro da sessão, servindo de contexto para as próximas
  perguntas.
- Troca e remoção do documento.
- Respostas em streaming, com indicação do que o agente está fazendo.

### Fora

- Reconhecimento óptico (OCR) de PDFs escaneados como imagem. O sistema detecta
  e avisa, mas não converte.
- Vários documentos ao mesmo tempo ou comparação entre arquivos.
- Login, contas e histórico entre sessões.
- Outros formatos: DOCX, XLSX, TXT, EPUB.
- Exportação da conversa.

## Decisões técnicas

### Stack

| Camada | Escolha | Motivo |
|---|---|---|
| Back-end | Python 3.14 + Flask | O ecossistema de IA em Python é o mais maduro; Flask basta para 7 endpoints |
| Agente | LangChain 1.3 (`create_agent`) | Dá o laço de ferramentas pronto, sem escrever o loop na mão |
| Modelo | Google Gemini (gemini-flash-lite-latest) | Rápido e barato no nível gratuito, com boa aderência à instrução de não extrapolar o documento |
| Leitura de PDF | pdfplumber | Melhor extração de texto sob licença permissiva (ver abaixo) |
| Busca | rank-bm25 | Busca local por palavras, sem depender de um segundo serviço externo |
| Front-end | Nuxt 4 + Nuxt UI 4 | Uma tela só, com streaming; o Nuxt entrega roteamento, build e proxy, e o Nuxt UI traz componentes prontos de chat e upload |

### Por que pdfplumber e não PyMuPDF

PyMuPDF é a biblioteca mais rápida e precisa de extração de PDF em Python, mas é
licenciada em **AGPL-3.0**: software acessado pela rede precisa ter o código
aberto, ou exige licença comercial paga. Para um projeto que pode virar público
ou fechado depois, isso amarra a decisão cedo demais.

**pdfplumber** (MIT, sobre pdfminer.six) entrega extração com posição, ordem de
leitura confiável e acesso página a página — exatamente o que o agente precisa
para citar a origem. Se o volume crescer e a velocidade virar problema, a troca
é isolada em `pdf_service.py`.

### Por que busca BM25 e não embeddings

O caminho usual seria dividir o documento, gerar embeddings e buscar por
similaridade. Isso exigiria um segundo serviço externo (ou um modelo local
pesado) só para a busca.

O BM25 roda no próprio processo, sem rede, e resolve bem a busca por termos —
que é o caso da maioria das perguntas sobre um documento específico. O agente
ainda pode ler a página inteira quando o trecho não bastar. Para documentos com
poucos trechos, o BM25 degenera (termos presentes em quase todos os blocos
recebem peso negativo), então há um segundo critério: contagem de termos
distintos por trecho.

### Por que Google Gemini

O projeto começou com Claude (Anthropic) e migrou para o Gemini a pedido do dono
do projeto, que já tinha uma chave do Google AI Studio. O `create_agent` do
LangChain aceita qualquer modelo, então a troca ficou isolada: saiu o
`langchain-anthropic`, entrou o `langchain-google-genai`, e o resto — agente,
ferramentas, streaming — não mudou. O modelo padrão é o `gemini-flash-lite-latest`
por ter a maior cota no nível gratuito.

### Por que não persistir nada

Documento e conversa vivem na memória do processo e são descartados na troca de
arquivo, na remoção, após 60 minutos de inatividade ou quando o servidor
reinicia.

Isso simplifica o projeto (sem banco, sem migração, sem limpeza) e reduz a
superfície de retenção de conteúdo alheio. O custo é claro: fechou, perdeu.

### Por que Nuxt UI

A primeira versão da interface tinha seis componentes escritos à mão. O Nuxt UI 4
já traz esses componentes, incluindo os de chat (`UChatMessages`, `UChatPrompt`,
`UChatPromptSubmit`, `UChatReasoning`), o `UFileUpload` com zona de arrastar e
soltar e o `USidebar` colapsável. Trocar o código próprio por eles eliminou cinco
componentes e todo o CSS de botões e cartões, e trouxe de brinde tema claro e
escuro, acessibilidade de teclado, rolagem automática e rótulos em português.

O layout usa o `USidebar`: identidade, envio e dados do documento à esquerda;
à direita, apenas a conversa. No mobile a barra vira overlay com botão de fechar;
recolhida no desktop, vira uma faixa só de ícones.

### Por que Flask e Nuxt separados

O agente precisa de Python. A interface fica melhor com um framework de
front-end. Em vez de o navegador falar com duas origens, o Nitro do Nuxt repassa
`/api/**` ao Flask — o que dispensa CORS e mantém a política de segurança de
conteúdo restrita a `'self'`.

## Segurança aplicada

| Controle | Onde |
|---|---|
| Validação do tipo real do arquivo (assinatura `%PDF-`), tamanho e páginas | `backend/app/services/pdf_service.py` |
| Validação da pergunta no back-end, não só no front | `backend/app/routes/conversas_routes.py` |
| Cabeçalhos CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy | `backend/app/middleware/seguranca.py` e `frontend/nuxt.config.ts` |
| Token de sessão exigido nas operações que alteram estado | `backend/app/middleware/seguranca.py` |
| Limite de requisições por IP | `backend/app/middleware/limites.py` |
| Erros sem stack trace na tela | `backend/app/__init__.py` |
| Log com ação, sessão e IP, sem conteúdo do documento nem texto das perguntas | `backend/app/utils/log.py` |
| Conteúdo do PDF tratado como dado, nunca como instrução ao agente | `backend/app/services/agente_service.py` |
| Chave da API só em variável de ambiente, `.env` fora do versionamento | `backend/app/config.py`, `.gitignore` |

A proteção contra injeção de instrução merece destaque: um PDF pode conter texto
dirigido ao modelo ("ignore as regras acima"). A instrução do sistema declara
que o documento é dado a ser analisado, não comando a ser obedecido.

## Limitações conhecidas

1. **O conteúdo do documento vai para a API do Google Gemini.** É inerente ao
   funcionamento. Não envie documento que você não possa compartilhar com um
   serviço de terceiros.
2. **Sem OCR.** PDF escaneado como imagem é aceito, mas não há texto para ler —
   a interface avisa.
3. **Instância única.** O estado em memória e o limite de requisições assumem um
   processo só. Rodar várias instâncias atrás de um balanceador exigiria
   armazenamento compartilhado.
4. **Sem login.** Qualquer pessoa com acesso ao endereço usa a aplicação. Para
   publicar na internet, isso precisa mudar.
5. **Cota do nível gratuito.** Cada pergunta gasta 2 a 3 chamadas ao modelo (o
   ciclo buscar → ler → responder), então rajadas de perguntas batem no limite
   por minuto do Gemini gratuito. O `flash-lite` tem a cota maior.

## O que foi testado

- 18 testes automatizados no back-end, com um modelo falso do LangChain (não
  consomem cota): upload válido e inválido, token ausente, sessão expirada,
  metadados, pergunta sem documento, pergunta vazia, conversa completa, remoção,
  cabeçalhos de segurança, busca por página, formato de resposta e tradução de
  erros do serviço de IA.
- Teste real de ponta a ponta com o Gemini: upload de um PDF de 10 páginas,
  pergunta respondida com citação da página correta, usando as ferramentas de
  busca e leitura.
- Instalação limpa a partir do `requirements.txt`, compilação de produção do
  front (`npm run build`) e responsividade verificada em 375px e 1440px.

## Ideias para depois

- OCR opcional para PDFs escaneados (Tesseract).
- Vários documentos por sessão, com busca entre eles.
- Exportar a conversa em Markdown.
- Persistência opcional, com login, para quem quiser manter histórico.
- Destacar no PDF o trecho que originou a resposta.
