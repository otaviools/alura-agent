// Camada unica de acesso a API do Docsy.
// Nenhum componente faz requisicao direta: tudo passa por aqui.

export interface DocumentoResumo {
  nomeArquivo: string
  tamanhoBytes: number
  totalPaginas: number
  paginasComTexto: number
  totalCaracteres: number
  possuiTexto: boolean
  criadoEm: string
  aviso?: string
}

export interface CredenciaisSessao {
  sessaoId: string
  tokenProtecao: string
  expiraEmMinutos: number
}

export interface EventoAgente {
  tipo: 'texto' | 'ferramenta' | 'fim' | 'erro'
  conteudo?: string
  nome?: string
  resposta?: string
  mensagem?: string
}

export class ErroApi extends Error {
  constructor(
    mensagem: string,
    readonly codigo = 'erro',
    readonly status = 0,
  ) {
    super(mensagem)
  }
}

const BASE = '/api'

/** Faz a requisicao com os cabecalhos da sessao e converte falha em ErroApi. */
async function requisitar(
  caminho: string,
  credenciais: CredenciaisSessao | null,
  opcoes: RequestInit = {},
): Promise<Response> {
  const resposta = await fetch(`${BASE}${caminho}`, {
    ...opcoes,
    headers: {
      ...opcoes.headers,
      ...(credenciais && {
        'X-Sessao': credenciais.sessaoId,
        'X-Token-Protecao': credenciais.tokenProtecao,
      }),
    },
  })

  if (resposta.ok) return resposta

  const corpo = await resposta.json().catch(() => null)
  throw new ErroApi(
    corpo?.mensagem ?? 'Nao foi possivel completar a operacao.',
    corpo?.erro ?? 'erro',
    resposta.status,
  )
}

export async function abrirSessao(): Promise<CredenciaisSessao> {
  const resposta = await requisitar('/sessoes', null, { method: 'POST' })
  return resposta.json()
}

export async function enviarDocumento(
  credenciais: CredenciaisSessao,
  arquivo: File,
): Promise<DocumentoResumo> {
  const formulario = new FormData()
  formulario.append('arquivo', arquivo)

  const resposta = await requisitar('/documentos', credenciais, {
    method: 'POST',
    body: formulario,
  })
  return resposta.json()
}

export async function removerDocumento(credenciais: CredenciaisSessao): Promise<void> {
  await requisitar('/documentos', credenciais, { method: 'DELETE' })
}

/**
 * Envia a pergunta e entrega os eventos da resposta conforme eles chegam.
 * O corpo vem no formato Server-Sent Events, uma linha "data:" por evento.
 */
export async function perguntar(
  credenciais: CredenciaisSessao,
  pergunta: string,
  aoReceber: (evento: EventoAgente) => void,
): Promise<void> {
  const resposta = await requisitar('/mensagens', credenciais, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pergunta }),
  })

  if (!resposta.body) throw new ErroApi('O servidor nao devolveu a resposta em fluxo.')

  const leitor = resposta.body.pipeThrough(new TextDecoderStream()).getReader()
  let pendente = ''

  while (true) {
    const { done, value } = await leitor.read()
    if (done) break

    pendente += value
    const blocos = pendente.split('\n\n')
    pendente = blocos.pop() ?? ''

    for (const bloco of blocos) {
      const linha = bloco.split('\n').find((item) => item.startsWith('data: '))
      if (!linha) continue
      try {
        aoReceber(JSON.parse(linha.slice(6)) as EventoAgente)
      } catch {
        // Evento incompleto ou malformado: ignora sem quebrar a conversa.
      }
    }
  }
}
