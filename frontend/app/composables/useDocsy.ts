// Estado compartilhado da aplicacao: sessao, documento e conversa.
// Os componentes so leem daqui e chamam estas acoes.

import {
  abrirSessao,
  enviarDocumento,
  ErroApi,
  perguntar,
  removerDocumento,
  type CredenciaisSessao,
  type DocumentoResumo,
} from '~/services/apiDocsy'

/** Formato de mensagem esperado pelos componentes de chat do Nuxt UI. */
export interface MensagemChat {
  id: string
  role: 'user' | 'assistant'
  parts: { type: 'text'; text: string }[]
  /** Raciocinio do agente (passos que ele deu no documento), exibido no
   *  UChatReasoning. Preenchido so nas respostas do assistente. */
  raciocinio?: string
  raciocinando?: boolean
  /** Repassados ao UChatMessage: destacam a bolha quando a resposta falha. */
  color?: 'error'
  variant?: 'soft'
}

/** Estados que o UChatPrompt entende. */
export type EstadoConversa = 'ready' | 'submitted' | 'streaming' | 'error'

// Cada ferramenta que o agente usa vira uma linha legivel no raciocinio.
const FERRAMENTAS: Record<string, string> = {
  buscar_trechos: 'Procurando os trechos relevantes no documento.',
  ler_pagina: 'Lendo o conteudo de uma pagina inteira.',
  informacoes_documento: 'Conferindo os dados do arquivo.',
}

export const useDocsy = () => {
  const credenciais = useState<CredenciaisSessao | null>('docsy-credenciais', () => null)
  const documento = useState<DocumentoResumo | null>('docsy-documento', () => null)
  const mensagens = useState<MensagemChat[]>('docsy-mensagens', () => [])
  const erro = useState<string>('docsy-erro', () => '')
  const enviandoArquivo = useState<boolean>('docsy-enviando', () => false)
  const estado = useState<EstadoConversa>('docsy-estado', () => 'ready')

  /** Garante uma sessao aberta e reabre quando ela expira no servidor. */
  async function comSessao<T>(operacao: (dados: CredenciaisSessao) => Promise<T>): Promise<T> {
    credenciais.value ??= await abrirSessao()
    try {
      return await operacao(credenciais.value)
    } catch (falha) {
      if (!(falha instanceof ErroApi) || falha.codigo !== 'sessao_invalida') throw falha
      credenciais.value = await abrirSessao()
      documento.value = null
      mensagens.value = []
      return operacao(credenciais.value)
    }
  }

  async function carregarArquivo(arquivo: File | null) {
    if (!arquivo) return
    erro.value = ''
    enviandoArquivo.value = true
    try {
      documento.value = await comSessao((dados) => enviarDocumento(dados, arquivo))
      mensagens.value = []
    } catch (falha) {
      erro.value = mensagemDe(falha)
    } finally {
      enviandoArquivo.value = false
    }
  }

  async function descartarDocumento() {
    erro.value = ''
    try {
      await comSessao(removerDocumento)
    } catch (falha) {
      erro.value = mensagemDe(falha)
    } finally {
      documento.value = null
      mensagens.value = []
      estado.value = 'ready'
    }
  }

  async function fazerPergunta(texto: string) {
    const pergunta = texto.trim()
    if (!pergunta || estado.value !== 'ready') return

    erro.value = ''
    estado.value = 'submitted'
    mensagens.value.push(criarMensagem('user', pergunta))
    mensagens.value.push(criarMensagem('assistant', '', { raciocinando: true }))

    // A mutacao precisa passar pelo proxy reativo, nao pelo objeto original.
    const resposta = mensagens.value[mensagens.value.length - 1]!

    try {
      await comSessao((dados) =>
        perguntar(dados, pergunta, (evento) => {
          if (evento.tipo === 'ferramenta') {
            // Cada passo do agente vira uma linha no raciocinio da resposta.
            const linha = FERRAMENTAS[evento.nome ?? ''] ?? 'Consultando o documento.'
            resposta.raciocinio = resposta.raciocinio
              ? `${resposta.raciocinio}\n${linha}`
              : linha
          } else if (evento.tipo === 'texto') {
            resposta.raciocinando = false
            estado.value = 'streaming'
            resposta.parts[0]!.text += evento.conteudo ?? ''
          } else if (evento.tipo === 'fim') {
            resposta.parts[0]!.text = evento.resposta ?? resposta.parts[0]!.text
          } else if (evento.tipo === 'erro') {
            marcarFalha(resposta, evento.mensagem ?? 'Nao foi possivel responder.')
          }
        }),
      )
    } catch (falha) {
      marcarFalha(resposta, mensagemDe(falha))
    } finally {
      estado.value = 'ready'
      resposta.raciocinando = false
    }
  }

  return {
    documento,
    mensagens,
    erro,
    enviandoArquivo,
    estado,
    carregarArquivo,
    descartarDocumento,
    fazerPergunta,
  }
}

function criarMensagem(
  role: MensagemChat['role'],
  text: string,
  extras: Partial<MensagemChat> = {},
): MensagemChat {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    parts: [{ type: 'text', text }],
    ...extras,
  }
}

function marcarFalha(mensagem: MensagemChat, texto: string) {
  mensagem.parts[0]!.text = texto
  mensagem.raciocinando = false
  mensagem.color = 'error'
  mensagem.variant = 'soft'
}

function mensagemDe(falha: unknown): string {
  if (falha instanceof ErroApi) return falha.message
  if (falha instanceof Error && falha.name === 'AbortError') return 'Consulta cancelada.'
  return 'Nao foi possivel falar com o servidor. Verifique se o back-end esta rodando.'
}
