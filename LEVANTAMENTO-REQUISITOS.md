# Levantamento de Requisitos — Agente de Atendimento de Logística e Envios

**Projeto:** Agente virtual de atendimento ao cliente — Empresa de Logística / Envios
**Versão:** 1.0
**Data:** 20/08/2026
**Responsável:** Otávio Santos

---

## 1. Contexto e objetivo

A empresa opera coleta, transporte e entrega de encomendas para clientes pessoa física e pessoa jurídica (e-commerces). O atendimento hoje concentra dúvidas repetitivas sobre prazo, rastreio, reembolso e abertura de sinistro, o que consome tempo da equipe humana e gera fila.

O objetivo é implantar um agente virtual que responda essas dúvidas com base na documentação oficial da empresa, consulte o status de pedidos e encaminhe para atendimento humano quando o caso exigir.

**Objetivos mensuráveis:**

| Indicador | Situação atual | Meta |
|---|---|---|
| Chamados resolvidos sem atendente | 0% | 60% em 6 meses |
| Tempo médio de primeira resposta | 4 h | Até 10 s no canal digital |
| Chamados sobre "onde está meu pedido" | 55% do volume | Reduzir para 20% |
| Satisfação do atendimento (CSAT) | 3,4 / 5 | 4,2 / 5 |

---

## 2. Escopo

### 2.1 Dentro do escopo

- Agente conversacional que responde perguntas com base em cinco documentos oficiais:
  - Política de envios
  - Procedimento de rastreamento de pedidos
  - Política de reembolsos e sinistros
  - Perguntas frequentes (FAQ)
  - Processo de reclamações e atendimento ao cliente
- Consulta de status de pedido por código de rastreio, número do pedido ou CPF/CNPJ do destinatário.
- Simulação de prazo e frete a partir de CEP de origem, CEP de destino, peso e dimensões.
- Abertura e acompanhamento de chamados: reclamação, solicitação de reembolso e registro de sinistro (extravio, avaria, roubo).
- Encaminhamento (handoff) para atendente humano com o histórico da conversa.
- Registro de todas as interações para auditoria e relatórios gerenciais.
- Canais: chat no site, WhatsApp e widget dentro do painel do cliente.

### 2.2 Fora do escopo

- Negociação de valores, descontos ou reembolso fora da tabela vigente.
- Aprovação final de sinistro — o agente registra e coleta evidências; a decisão é do analista.
- Alteração de endereço de entrega após a mercadoria estar em rota (redirecionamento é feito pela transportadora).
- Emissão de nota fiscal, boleto ou documentos fiscais.
- Atendimento por voz (telefone) e por e-mail na primeira versão.
- Integração com marketplaces (Mercado Livre, Shopee) na primeira versão.
- Rastreamento em tempo real por GPS do veículo.

---

## 3. Premissas

1. Os cinco documentos existem, estão aprovados pela área de Operações e Jurídico, e são fornecidos em formato de texto (Markdown ou PDF pesquisável).
2. Os documentos são atualizados pela equipe de Operações; o agente sempre responde com base na versão mais recente publicada.
3. Existe uma API de rastreamento interna (TMS) disponível, com autenticação por token e resposta em JSON.
4. O cadastro de pedidos e clientes é a fonte da verdade; o agente não cria nem altera dados cadastrais.
5. A equipe de atendimento humano permanece disponível em horário comercial (seg. a sex., 8h às 18h) para receber os encaminhamentos.
6. O cliente já está autenticado quando usa o widget do painel; nos canais públicos, é necessário validar identidade antes de expor dados do pedido.
7. O volume estimado é de 8.000 conversas/mês, com pico de 3x em datas comerciais (Black Friday, Natal).
8. O tratamento de dados pessoais segue a LGPD, com a empresa como controladora.

### 3.1 Restrições

- O agente não pode inventar informação: se a resposta não estiver na base de conhecimento ou nas APIs, deve dizer que não sabe e oferecer encaminhamento.
- Orçamento de infraestrutura e custo por conversa definidos pela diretoria; o agente deve operar dentro do teto contratado do provedor de modelo.
- Prazo de implantação da primeira versão: 90 dias.

---

## 4. Stakeholders e personas

| Perfil | Necessidade principal |
|---|---|
| Destinatário (pessoa física) | Saber onde está a encomenda e o que fazer quando atrasa |
| Cliente contratante (e-commerce) | Consultar vários pedidos, abrir sinistros em lote, ter previsibilidade de SLA |
| Atendente de suporte | Receber o caso já qualificado, com histórico e dados do pedido |
| Analista de sinistros | Receber o registro com evidências completas para decidir |
| Operações / Qualidade | Manter os documentos atualizados e medir a qualidade das respostas |
| Jurídico / DPO | Garantir aderência à LGPD e ao Código de Defesa do Consumidor |

---

## 5. Interface

### 5.1 Canais

| Canal | Descrição | Autenticação |
|---|---|---|
| Chat web (site público) | Widget flutuante no canto inferior direito | Validação por código de rastreio + confirmação de dado do pedido |
| WhatsApp | Número oficial da empresa, via API | Número do remetente + validação de dado do pedido |
| Painel do cliente | Widget dentro da área logada | Sessão já autenticada |

### 5.2 Elementos da interface conversacional

- **Mensagem de abertura:** identificação clara de que se trata de um agente virtual, com as opções principais (rastrear, prazo e frete, reembolso, sinistro, reclamação, falar com atendente).
- **Menu de atalhos:** botões de resposta rápida para as cinco intenções mais comuns.
- **Campo de entrada de texto livre:** aceita pergunta em linguagem natural.
- **Cartão de rastreamento:** exibe código, status atual, transportadora, previsão de entrega e linha do tempo com os eventos (postado, em trânsito, saiu para entrega, entregue).
- **Formulário guiado:** para abertura de sinistro e reembolso, com campos obrigatórios e upload de anexos (foto da avaria, nota fiscal, laudo).
- **Indicador de origem da resposta:** quando a resposta vem de um documento, exibe qual documento e a seção citada.
- **Botão "falar com atendente":** visível o tempo todo.
- **Protocolo:** exibido ao final de qualquer registro de chamado, com opção de copiar.

### 5.3 Fluxo principal (rastreamento)

1. Cliente entra no chat e escolhe "Rastrear pedido".
2. Agente pede o código de rastreio ou número do pedido.
3. Agente valida a identidade solicitando um dado adicional (CEP de entrega ou últimos dígitos do CPF).
4. Agente consulta a API de rastreamento.
5. Agente devolve o cartão de rastreamento com a linha do tempo.
6. Se houver atraso além do prazo contratado, o agente já oferece abrir reclamação.
7. Cliente encerra ou segue para outra intenção.

### 5.4 Fluxos de exceção

- Código não encontrado → agente confirma a digitação, sugere verificar com o remetente e oferece encaminhamento.
- Três tentativas de validação sem sucesso → encaminhamento obrigatório para atendente humano.
- API indisponível → agente informa a indisponibilidade, registra o pedido de consulta e oferece retorno por e-mail.

### 5.5 Requisitos de acessibilidade e apresentação

- Contraste mínimo AA (WCAG 2.1), navegação completa por teclado e compatibilidade com leitor de tela.
- Layout responsivo para telas a partir de 320 px.
- Linguagem simples, frases curtas, sem jargão logístico não explicado.

---

## 6. Regras de negócio

| ID | Regra |
|---|---|
| RN01 | O agente só responde sobre assuntos de logística, envios, pedidos e atendimento da empresa. Assuntos fora do domínio recebem recusa educada com redirecionamento. |
| RN02 | Toda resposta sobre política, prazo, taxa ou reembolso deve ter origem em um dos cinco documentos oficiais. Sem fonte, o agente declara que não sabe. |
| RN03 | Dados de pedido só são exibidos após validação de identidade, exceto no painel logado. |
| RN04 | O prazo de entrega é contado em dias úteis a partir da postagem, conforme a modalidade contratada (Expresso, Padrão, Econômico). |
| RN05 | Pedido é considerado atrasado quando ultrapassa o prazo contratado; a partir daí, o cliente pode abrir reclamação. |
| RN06 | Pedido é considerado extraviado após 7 dias úteis sem movimentação na modalidade Expresso e 15 dias úteis nas modalidades Padrão e Econômico. Só então é possível abrir sinistro por extravio. |
| RN07 | Sinistro por avaria exige registro em até 7 dias corridos após a entrega, com foto do produto, foto da embalagem e nota fiscal. |
| RN08 | O valor de indenização é limitado ao valor declarado na nota fiscal, respeitando o teto da modalidade contratada. |
| RN09 | O prazo de análise de sinistro é de até 30 dias corridos a partir do registro completo, conforme a política vigente. |
| RN10 | Reembolso aprovado é devolvido pelo mesmo meio de pagamento, em até 10 dias úteis após a aprovação. |
| RN11 | Frete não é reembolsado quando a entrega foi concluída dentro do prazo, salvo avaria comprovada. |
| RN12 | Tentativa de entrega frustrada gera nova tentativa em até 2 vezes; após isso, a encomenda retorna ao remetente e o frete de retorno é cobrado conforme a política de envios. |
| RN13 | Toda reclamação, sinistro ou pedido de reembolso gera um protocolo único e rastreável. |
| RN14 | Reclamações críticas (extravio de carga de alto valor, ameaça de ação judicial, menção a órgão de defesa do consumidor) são encaminhadas imediatamente ao atendente humano. |
| RN15 | O SLA de primeira resposta humana após encaminhamento é de 4 horas úteis; o de solução, 5 dias úteis. |
| RN16 | O agente não altera endereço de entrega, não cancela envio em rota e não autoriza crédito. |
| RN17 | O agente identifica-se como assistente virtual no início de toda conversa e sempre que perguntado. |
| RN18 | Dados pessoais coletados são usados apenas para o atendimento e retidos conforme a política de privacidade; o agente nunca solicita senha, dado bancário completo ou número completo de cartão. |
| RN19 | Áreas de risco e localidades com restrição de entrega seguem a lista publicada na política de envios; nessas regiões, o prazo é acrescido conforme tabela. |
| RN20 | Se o cliente pedir atendimento humano de forma explícita, o agente encaminha sem insistir em resolver sozinho. |

---

## 7. Requisitos funcionais

### 7.1 Base de conhecimento e respostas

| ID | Requisito | Prioridade |
|---|---|---|
| RF01 | O sistema deve ingerir os cinco documentos oficiais, dividi-los em trechos e indexá-los para busca semântica. | Alta |
| RF02 | O sistema deve responder perguntas em linguagem natural usando os trechos recuperados da base de conhecimento. | Alta |
| RF03 | O sistema deve citar o documento e a seção de origem em respostas sobre políticas e prazos. | Alta |
| RF04 | O sistema deve informar que não possui a informação quando não houver trecho relevante, e oferecer encaminhamento. | Alta |
| RF05 | O sistema deve permitir atualizar os documentos e reindexar a base sem indisponibilidade do atendimento. | Média |
| RF06 | O sistema deve manter versionamento dos documentos, registrando qual versão respondeu cada interação. | Média |

### 7.2 Rastreamento

| ID | Requisito | Prioridade |
|---|---|---|
| RF07 | O sistema deve consultar o status de um pedido por código de rastreio, número do pedido ou CPF/CNPJ. | Alta |
| RF08 | O sistema deve exibir a linha do tempo dos eventos do pedido, com data, hora e localidade. | Alta |
| RF09 | O sistema deve validar a identidade do solicitante antes de exibir dados do pedido em canais públicos. | Alta |
| RF10 | O sistema deve calcular e informar se o pedido está dentro ou fora do prazo contratado. | Alta |
| RF11 | O sistema deve permitir que o cliente opte por receber notificação de mudança de status no canal em uso. | Baixa |
| RF12 | O sistema deve tratar código inexistente, código de outra transportadora e código com formato inválido com mensagens específicas. | Alta |

### 7.3 Prazos e fretes

| ID | Requisito | Prioridade |
|---|---|---|
| RF13 | O sistema deve simular prazo e valor de frete a partir de CEP de origem, CEP de destino, peso e dimensões. | Média |
| RF14 | O sistema deve apresentar as modalidades disponíveis (Expresso, Padrão, Econômico) com prazo e valor de cada uma. | Média |
| RF15 | O sistema deve informar restrições de entrega da localidade consultada, quando houver. | Média |

### 7.4 Reembolsos e sinistros

| ID | Requisito | Prioridade |
|---|---|---|
| RF16 | O sistema deve conduzir um formulário guiado para abertura de sinistro, coletando tipo de ocorrência, descrição, valor declarado e anexos. | Alta |
| RF17 | O sistema deve validar a elegibilidade do sinistro antes de abrir o registro (prazo, tipo de ocorrência, documentos obrigatórios). | Alta |
| RF18 | O sistema deve aceitar upload de imagens e PDF de até 10 MB por arquivo, com no máximo 5 arquivos por chamado. | Alta |
| RF19 | O sistema deve gerar protocolo e informar o prazo de análise ao concluir o registro. | Alta |
| RF20 | O sistema deve permitir consultar o andamento de um sinistro ou reembolso pelo número de protocolo. | Alta |
| RF21 | O sistema deve explicar as regras de indenização e os limites por modalidade quando o cliente perguntar. | Alta |

### 7.5 Reclamações e atendimento humano

| ID | Requisito | Prioridade |
|---|---|---|
| RF22 | O sistema deve registrar reclamações com categoria, descrição, pedido relacionado e canal de origem. | Alta |
| RF23 | O sistema deve classificar a criticidade da reclamação conforme a RN14 e priorizar o encaminhamento. | Alta |
| RF24 | O sistema deve encaminhar a conversa para atendente humano, transferindo histórico completo, dados do cliente e do pedido. | Alta |
| RF25 | O sistema deve informar o SLA de retorno ao encaminhar. | Alta |
| RF26 | O sistema deve enfileirar o atendimento fora do horário comercial e informar o horário previsto de retorno. | Média |
| RF27 | O sistema deve solicitar avaliação de satisfação ao final da conversa. | Média |

### 7.6 Administração e observabilidade

| ID | Requisito | Prioridade |
|---|---|---|
| RF28 | O sistema deve registrar toda interação (pergunta, resposta, fontes usadas, latência, custo). | Alta |
| RF29 | O sistema deve oferecer painel com volume de conversas, taxa de resolução sem humano, principais intenções e perguntas sem resposta. | Média |
| RF30 | O sistema deve listar as perguntas que não obtiveram resposta, para alimentar a atualização dos documentos. | Média |
| RF31 | O sistema deve permitir configurar mensagens fixas (saudação, indisponibilidade, encerramento) sem alteração de código. | Média |
| RF32 | O sistema deve permitir desligar o agente e direcionar todo o tráfego para o atendimento humano (chave de contingência). | Alta |
| RF33 | O sistema deve exportar o histórico de uma conversa em PDF a pedido do cliente ou do atendente. | Baixa |

---

## 8. Requisitos não funcionais

### 8.1 Desempenho

| ID | Requisito |
|---|---|
| RNF01 | Tempo de primeira resposta do agente até 3 segundos no percentil 95. |
| RNF02 | Consulta de rastreamento concluída em até 5 segundos, incluindo a chamada à API do TMS. |
| RNF03 | Suportar 150 conversas simultâneas em operação normal e 450 em pico sazonal. |
| RNF04 | Resposta em streaming, com o primeiro trecho exibido em até 1,5 segundo. |

### 8.2 Disponibilidade e confiabilidade

| ID | Requisito |
|---|---|
| RNF05 | Disponibilidade mensal de 99,5% para o canal de chat. |
| RNF06 | Degradação controlada: se a API de rastreamento cair, o agente continua respondendo dúvidas de política e registra a consulta pendente. |
| RNF07 | Retentativa automática com backoff em falhas de integração, com no máximo 3 tentativas. |
| RNF08 | Backup diário dos registros de conversa e chamados, com retenção de 12 meses e restauração testada trimestralmente. |

### 8.3 Segurança e privacidade

| ID | Requisito |
|---|---|
| RNF09 | Tráfego exclusivamente por HTTPS (TLS 1.2 ou superior). |
| RNF10 | Dados pessoais criptografados em repouso. |
| RNF11 | Mascaramento de CPF, CNPJ e telefone nos logs e no painel administrativo. |
| RNF12 | Controle de acesso por perfil (atendente, supervisor, administrador, auditor). |
| RNF13 | Aderência à LGPD: base legal registrada, atendimento a pedidos de acesso e exclusão, e política de retenção documentada. |
| RNF14 | Proteção contra injeção de instrução: conteúdo vindo de documentos, anexos e APIs é tratado como dado, nunca como comando. |
| RNF15 | Limite de requisições por sessão e por número de origem, para conter abuso e automação. |
| RNF16 | Trilha de auditoria imutável de acessos a dados de pedido e de alterações na base de conhecimento. |

### 8.4 Qualidade das respostas

| ID | Requisito |
|---|---|
| RNF17 | Taxa de resposta com fonte correta igual ou superior a 95% em conjunto de avaliação com no mínimo 200 perguntas reais. |
| RNF18 | Taxa de resposta sem base documental abaixo de 1%. |
| RNF19 | Conjunto de testes automatizados de regressão executado a cada alteração de prompt, modelo ou base de conhecimento. |
| RNF20 | Revisão humana amostral de 5% das conversas por semana. |

### 8.5 Usabilidade

| ID | Requisito |
|---|---|
| RNF21 | Respostas em português brasileiro, com no máximo 4 frases por bloco e listas quando houver etapas. |
| RNF22 | Aderência ao WCAG 2.1 nível AA. |
| RNF23 | Funcionamento nas duas últimas versões de Chrome, Edge, Firefox e Safari, em desktop e mobile. |
| RNF24 | Tom cordial e direto; termos técnicos de logística explicados na primeira menção. |

### 8.6 Manutenibilidade e operação

| ID | Requisito |
|---|---|
| RNF25 | Prompts, regras e mensagens fixas versionados em repositório, com histórico de alterações. |
| RNF26 | Atualização da base de conhecimento executável pela equipe de Operações, sem envolvimento de desenvolvimento. |
| RNF27 | Ambientes separados de desenvolvimento, homologação e produção. |
| RNF28 | Custo médio por conversa monitorado, com alerta quando ultrapassar o teto definido. |
| RNF29 | Camada de integração com o provedor de modelo isolada, permitindo troca de modelo sem reescrever a aplicação. |
| RNF30 | Documentação técnica de instalação, configuração e operação mantida junto ao código. |

---

## 9. Estrutura esperada da base de conhecimento

| Documento | Conteúdo mínimo | Responsável | Revisão |
|---|---|---|---|
| Política de envios | Modalidades, prazos por região, tabela de frete, restrições de conteúdo, embalagem, tentativas de entrega, devolução ao remetente | Operações | Trimestral |
| Procedimento de rastreamento de pedidos | Significado de cada status, prazos entre eventos, o que fazer em cada situação, canais de consulta | Operações | Semestral |
| Política de reembolsos e sinistros | Tipos de sinistro, prazos de abertura, documentos exigidos, limites de indenização, prazos de análise e pagamento | Jurídico + Operações | Trimestral |
| Perguntas frequentes | Perguntas reais dos clientes com resposta curta e link para o documento completo | Atendimento | Mensal |
| Processo de reclamações e atendimento ao cliente | Canais, horários, SLAs, níveis de escalonamento, tratamento de casos críticos, ouvidoria | Atendimento | Semestral |

---

## 10. Critérios de aceite da primeira versão

1. O agente responde corretamente a 90% de um roteiro de 50 perguntas homologado pela equipe de atendimento.
2. Rastreamento funciona nos três canais previstos, com validação de identidade.
3. Abertura de sinistro gera protocolo válido no sistema de chamados, com anexos preservados.
4. Encaminhamento para humano transfere o histórico completo e é confirmado pelo atendente.
5. Nenhuma resposta sobre política é dada sem citação de documento.
6. Painel exibe volume, taxa de resolução e lista de perguntas sem resposta.
7. Chave de contingência desliga o agente e redireciona o tráfego em menos de 1 minuto.
8. Relatório de conformidade LGPD aprovado pelo DPO.

---

## 11. Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Documentos desatualizados gerando resposta errada | Alto | Revisão periódica obrigatória e exibição da data de vigência na resposta |
| Instabilidade da API de rastreamento | Alto | Degradação controlada e fila de consultas pendentes |
| Cliente irritado ficando preso no agente | Alto | Botão de atendente sempre visível e encaminhamento por detecção de insatisfação |
| Vazamento de dados de pedido por validação fraca | Alto | Dupla checagem de identidade e limite de tentativas |
| Custo por conversa acima do previsto em pico sazonal | Médio | Monitoramento de custo, cache de perguntas frequentes e limite por sessão |
| Resistência da equipe de atendimento | Médio | Envolver atendentes na curadoria da FAQ e no roteiro de testes |

---

## 12. Glossário

- **Sinistro:** ocorrência de extravio, avaria ou roubo da encomenda.
- **Extravio:** encomenda sem movimentação e sem localização após o prazo definido na RN06.
- **Avaria:** dano físico ao produto ou à embalagem constatado na entrega.
- **Handoff:** transferência da conversa do agente para um atendente humano.
- **SLA:** prazo máximo acordado para primeira resposta ou solução.
- **TMS:** sistema de gestão de transporte, fonte dos dados de rastreamento.
- **Protocolo:** identificador único de um chamado aberto pelo cliente.
- **Valor declarado:** valor da mercadoria informado no envio, base para indenização.
