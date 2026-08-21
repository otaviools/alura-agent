// Configuracao do front-end do Docsy (Nuxt 4 + Nuxt UI).
const backend = process.env.DOCSY_BACKEND_URL || 'http://127.0.0.1:5000'
const emDesenvolvimento = process.env.NODE_ENV !== 'production'

// O recarregamento a quente do Nuxt exige eval e WebSocket; em producao a
// politica fica estrita.
const politicaDeSeguranca = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${emDesenvolvimento ? " 'unsafe-eval'" : ''}`,
  "style-src 'self' 'unsafe-inline'",
  // O Nuxt UI cria workers a partir de blob: para realce de codigo.
  "worker-src 'self' blob:",
  "font-src 'self'",
  "img-src 'self' data:",
  `connect-src 'self'${emDesenvolvimento ? ' ws: http://localhost:* http://127.0.0.1:*' : ''}`,
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
].join('; ')

export default defineNuxtConfig({
  compatibilityDate: '2026-08-20',
  devtools: { enabled: false },

  modules: ['@nuxt/ui'],
  css: ['~/assets/css/principal.css'],

  icon: {
    // O endpoint padrao do Nuxt Icon e /api/_nuxt_icon, que colidiria com o
    // proxy de /api/** para o back-end Flask.
    localApiEndpoint: '/_icones',
    // Sem isto o servidor tenta baixar cada icone da API publica do Iconify a
    // cada renderizacao. Com "local" ele usa o pacote @iconify-json/lucide que
    // ja esta instalado, e a aplicacao funciona sem internet.
    serverBundle: 'local',
    clientBundle: { scan: true },
  },

  app: {
    head: {
      htmlAttrs: { lang: 'pt-BR' },
      title: 'Docsy',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Envie um PDF e pergunte sobre o conteudo dele.' },
      ],
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
    },
  },

  // Todo o trafego de API passa pelo proprio dominio do front, que repassa ao
  // back-end Flask. Assim o navegador nunca fala com uma segunda origem.
  routeRules: {
    '/api/**': { proxy: `${backend}/api/**` },
    '/**': {
      headers: {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'Referrer-Policy': 'no-referrer',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': politicaDeSeguranca,
      },
    },
  },
})
