# Plano Arquitetural e Técnico — Garage Route 66

> **Atualização:** este documento é do plano inicial. A estrutura atual (`src/`, `public/`, `dist/`, build com Tailwind compilado e `client-config.json`) está descrita em [ARCHITECTURE.md](../ARCHITECTURE.md). Onde houver divergência de caminhos (`assets/...`, `index.html` na raiz), vale o ARCHITECTURE.md. Para publicar, o diretório de saída agora é `dist` e o comando de build é `node scripts/build.mjs` (não é mais "sem build").


**Papel:** CTO  
**Projeto:** Site Institucional e Captação Local — Garage Route 66 (Parelheiros, São Paulo - SP)  
**Escopo avaliado:** `index.html` (versão atual: 869 linhas, arquivo único)  
**Princípio norteador:** Arquitetura estática enxuta, carregamento instantâneo em 4G mobile, SEO local forte, zero overengineering e manutenção simples.

---

## 1. Diagnóstico Técnico da Versão Atual

### Pontos Fortes
- **Foco claro em conversão local:** múltiplos CTAs para WhatsApp com mensagens pré-preenchidas, modal de pré-orçamento estruturado, botão flutuante e mapa com rota direta no Google Maps.
- **Identidade visual bem definida:** estética automotiva escura (`#141518` / `#DC2626`), tipografia coerente (`Oswald` + `Inter`) e escudo Route 66 vetorial (SVG).
- **Zero backend desnecessário:** 100% estático, hospedável a custo zero com alta disponibilidade e baixa superfície de ataque.
- **Boas iniciativas pontuais:** uso de `rel="noopener noreferrer"` nos links externos existentes, `loading="lazy"` no `iframe` do mapa e indicador de aberto/fechado.

### Riscos Reais e Dívidas Técnicas
| Severidade | Problema Identificado | Impacto Real |
| :--- | :--- | :--- |
| **Crítica** | **Tailwind Play CDN em produção** (`cdn.tailwindcss.com`) | Baixa e executa o compilador JS inteiro no navegador (~350 KB), bloqueia renderização, gera FOUC/CLS e degrada o LCP em celulares 4G. A própria Tailwind desaconselha uso em produção. |
| **Crítica** | **Conteúdo fictício apresentado como real** (depoimentos marcados como *"Avaliação verificada • Google"* sendo textos inventados; foto do Hero via Unsplash com fallback para `placehold.co`) | Risco jurídico (CDC — publicidade enganosa), perda de confiança do cliente local e dependência de URL externa sem `width`/`height` (causando CLS). |
| **Alta** | **Ausência de SEO local estruturado e Open Graph** | Sem `Schema.org` (`AutoRepair`), sem `canonical`, `robots.txt`, `sitemap.xml`, favicon e tags `og:*`. Prejudica o ranqueamento em *"oficina mecânica Parelheiros"* e deixa o link sem preview ao compartilhar no WhatsApp. |
| **Média** | **Bugs de UX e acessibilidade** | Header fixo (`80px`) cobre parte das seções ao navegar por âncoras (falta `scroll-margin-top`); não há menu mobile (`< 768px`); `copyAddress()` usa `document.execCommand('copy')` (obsoleto); `animate-[fadeIn_0.2s_ease-out]` no modal referencia keyframe inexistente; modal não trava scroll do `body` nem possui atributos ARIA; ano hardcoded em `2025`. |
| **Média** | **Manutenibilidade e duplicação** | HTML único de 869 linhas misturando markup, config Tailwind, `onclick` inline e JS. O número do WhatsApp está hardcoded em 10 pontos do HTML + 1 no JS. `showToast()` usa `innerHTML` em vez de `textContent`. |

---

## 2. Decisão de Arquitetura — Fase 1

### Decisão: Site Estático Multi-Arquivo com Tailwind CLI Compilado + JS Vanilla
- **O que fica de fora:** nenhum framework SPA (React, Next.js, Vue), nenhum CMS pesado, nenhum backend/banco de dados.
- **Decisão sobre CSS (Tailwind compilado vs. CSS puro):** **usar Tailwind CSS compilado via CLI** (aproveitando o Node 24 disponível no ambiente de dev), gerando um único arquivo `assets/css/styles.css` minificado (~12–18 KB).
  - **Por quê:** preserva 100% do design já aprovado sem o retrabalho e risco de regressão de reescrever tudo em CSS manual, elimina o Play CDN em produção e entrega performance idêntica a CSS escrito à mão.
  - **Manutenção simples para o dono:** o artefato final é **HTML + CSS + JS puros**. Para alterar textos, horários, telefone, serviços ou trocar fotos, **não é necessário rodar Node nem build**. O build (`npm run build`) só é executado quando um dev alterar layout ou adicionar novas classes utilitárias.

### Estrutura de Diretórios Recomendada
```text
garageroute66/
├── index.html                  # HTML semântico limpo, sem CDN e sem onclick inline
├── package.json                # Apenas tailwindcss CLI (devDependency) + scripts dev/build
├── robots.txt                  # Diretivas de indexação
├── sitemap.xml                 # Mapa do site para Google Search Console
├── _headers                    # Cabeçalhos de segurança (Cloudflare Pages / Netlify)
├── src/
│   └── input.css               # Entrada Tailwind + tokens de tema + @keyframes fadeIn
├── assets/
│   ├── css/
│   │   └── styles.css          # CSS compilado e minificado (gerado pelo build)
│   ├── js/
│   │   └── main.js             # JS vanilla (defer) com config centralizada no topo
│   ├── img/
│   │   ├── hero-oficina.webp   # Foto real da oficina (otimizada, dimensões explícitas)
│   │   └── og-cover.jpg        # Capa 1200x630 para WhatsApp / Open Graph
│   └── icons/
│       └── favicon.svg         # Escudo Route 66 vetorial
└── docs/
    └── arquitetura-cto.md
```

### Hospedagem e Domínio (Pragmático)
- **Hospedagem:** **Cloudflare Pages** (preferencial — plano gratuito, CDN com ponto de presença em São Paulo, SSL automático, suporte nativo a `_headers`). Alternativas equivalentes: Netlify ou Vercel.
- **Domínio:** registrar `garageroute66.com.br` no Registro.br (~R$ 40/ano) e apontar para a hospedagem com redirecionamento `www` -> apex (ou vice-versa) e HTTPS forçado.

---

## 3. Requisitos Técnicos Obrigatórios para o Dev Full (Fase 1)

### 3.1 Build, CSS e Performance
1. Remover `<script src="https://cdn.tailwindcss.com"></script>` e o bloco `tailwind.config` inline.
2. Configurar `package.json` com Tailwind CLI e scripts `dev` (watch) e `build` (minify) gerando `assets/css/styles.css`.
3. Definir `@keyframes fadeIn` (ou transição CSS nativa) em `src/input.css` para a abertura do modal.
4. Mover todo o JavaScript para `assets/js/main.js` carregado com `<script src="assets/js/main.js" defer></script>`, removendo todos os atributos `onclick` e `onsubmit` inline.
5. Garantir na imagem do Hero: atributos explícitos `width` e `height`, `fetchpriority="high"` e fallback local seguro (remover dependência de `placehold.co`).

### 3.2 SEO Local, Metadados e Identidade
1. **JSON-LD `Schema.org` (`@type: "AutoRepair"`):** incluir no `<head>` com `name`, `description`, `url`, `telephone`, `priceRange`, `image`, `address` (`PostalAddress` completo de Parelheiros), `geo` (`GeoCoordinates`), `areaServed` (Parelheiros, Vargem Grande, Colônia, Marsilac, Zona Sul - SP), `openingHoursSpecification` (Seg–Sex 08:00–18:00, Sáb 08:00–12:00) e `sameAs` (Instagram + link do Google Meu Negócio).
   - *Regra:* só incluir `aggregateRating` no JSON-LD quando a nota e contagem estiverem confirmadas no perfil real do Google Meu Negócio.
2. **Open Graph & Twitter Cards:** adicionar `og:type`, `og:locale` (`pt_BR`), `og:site_name`, `og:title`, `og:description`, `og:url`, `og:image` (1200x630), `og:image:alt` e `twitter:card` (`summary_large_image`).
3. **Tags técnicas essenciais:** `<link rel="canonical">`, `<meta name="robots" content="index, follow">`, `<meta name="theme-color" content="#141518">`.
4. **Favicon SVG:** criar `assets/icons/favicon.svg` baseado no escudo Route 66 e referenciar com `<link rel="icon" type="image/svg+xml" href="assets/icons/favicon.svg">`.
5. **Arquivos de rastreamento:** criar `robots.txt` e `sitemap.xml` na raiz (com URL base configurável para o domínio definitivo).

### 3.3 Correções de JS, UX e Acessibilidade
1. **Offset do Header fixo:** aplicar `scroll-padding-top: 5.5rem` no `html` (ou `scroll-mt-24` em `#avaliacoes`, `#servicos`, `#diferenciais`, `#localizacao`) para evitar que o header fixo cubra o título das seções.
2. **Navegação mobile:** adicionar botão menu hambúrguer acessível (`aria-expanded`, `aria-controls`) com menu colapsável em telas `< md`, incluindo links de seção e botão de Pré-Orçamento.
3. **Clipboard moderno:** reescrever `copyAddress()` com `navigator.clipboard.writeText()` (`async/await`) + fallback via `textarea` fora da tela, exibindo toast de erro (`type = 'error'`) caso ambos falhem.
4. **Modal robusto e acessível:**
   - Adicionar `role="dialog"`, `aria-modal="true"`, `aria-labelledby`.
   - Travar scroll do fundo (`overflow-hidden` no `body`) ao abrir e liberar ao fechar.
   - Salvar o elemento com foco antes de abrir e devolver o foco ao fechar.
   - Resetar o formulário após envio para o WhatsApp.
   - Opcional recomendado: permitir que os cards de serviço abram o modal já com o serviço pré-selecionado ou mantenham link direto para WhatsApp gerado via config única.
5. **Status de funcionamento (Aberto/Fechado):** substituir `new Date(now.toLocaleString(...))` por `Intl.DateTimeFormat('en-US', { timeZone: 'America/Sao_Paulo', weekday: 'short', hour: '2-digit', hourCycle: 'h23' }).formatToParts(now)` (sem parsing frágil de string) e atualizar a cada 60 segundos.
6. **Ano dinâmico no rodapé:** substituir `© 2025` por `<span id="current-year">2026</span>` preenchido dinamicamente com `new Date().getFullYear()`.
7. **Fonte única de contato:** centralizar `WHATSAPP_NUMBER`, endereço e mensagens padrão em um objeto `SITE_CONFIG` no topo de `assets/js/main.js` (e aplicar nos botões via `data-whatsapp-msg` / `data-action`), eliminando 10 repetições manuais no HTML.
8. **Tratamento de conteúdo provisório:** remover o rótulo enganoso *"Avaliação verificada • Google"* de textos fictícios e deixar os depoimentos claramente sinalizados para substituição antes do deploy (ou exibir CTA direto *"Ver avaliações no Google"* enquanto os depoimentos reais não chegam).

### 3.4 Segurança Básica
1. **Links externos:** manter `target="_blank" rel="noopener noreferrer"` em todos os links externos e `'noopener,noreferrer'` em `window.open()`.
2. **Prevenção de XSS no Toast:** substituir `toast.innerHTML` por criação segura de nós DOM (`document.createElement` + `textContent`) e adicionar `aria-live="polite"` no `#toast-box`.
3. **Headers HTTP (`_headers`):** incluir `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` e `Permissions-Policy: camera=(), microphone=(), geolocation=()`.
4. **Iframe do mapa:** manter `loading="lazy"`, `referrerpolicy="no-referrer-when-downgrade"` e `title` descritivo.

---

## 4. Checklist de Dados Reais (Obrigatório Antes de Publicar)

O dono da oficina deve fornecer e validar os itens abaixo antes do lançamento oficial:

### Bloqueadores de Publicação (Go / No-Go)
- [ ] **Fotos reais da oficina (3 a 5 fotos em boa resolução, orientação horizontal):** fachada com identificação Route 66, interior/elevadores e atendimento/diagnóstico (para substituir a foto do Unsplash e gerar a capa `og-cover.jpg`).
- [ ] **Perfil do Google Meu Negócio:** link oficial do perfil no Google Maps/Search, confirmação da nota atual e da quantidade exata de avaliações.
- [ ] **Depoimentos reais (3 a 6 avaliações):** textos reais copiados do Google Meu Negócio com os nomes conforme exibidos publicamente, substituindo 100% dos depoimentos fictícios.
- [ ] **WhatsApp e telefone principal:** confirmar se `+55 (11) 94379-6788` está correto e ativo para ligações e WhatsApp.
- [ ] **Endereço e pino no mapa:** confirmar `Rua Bem Te Vi, 32 – Parelheiros, São Paulo - SP, CEP 04896-310` e validar se o marcador do mapa aponta exatamente para a entrada da oficina (fornecer coordenadas exatas se houver desvio).
- [ ] **Horários reais de funcionamento:** confirmar Seg–Sex `08h às 18h`, Sáb `08h às 12h`, Dom `Fechado` (confirmar se fecha para almoço e como opera em feriados).

### Conferência Comercial
- [ ] **Instagram oficial:** confirmar se o perfil ativo é `@garageroute66_`.
- [ ] **Catálogo de serviços:** validar se os 6 serviços listados refletem exatamente o que a oficina executa (ex.: atende importados? faz cabeçote/embreagem/ABS? falta algum serviço forte como ar-condicionado ou alinhamento?).
- [ ] **Garantia e pagamento:** confirmar prazo de garantia (peças e mão de obra) e formas de pagamento aceitas (Pix, débito, parcelamento no crédito) para incluir na copy.
- [ ] **Domínio oficial:** aprovar e registrar o domínio (ex.: `garageroute66.com.br`) para preencher `canonical`, `og:url`, `sitemap.xml` e Schema.org.

---

## 5. Roadmap de Evolução

### Fase 1 — Lançamento Enxuto e Sólido (Atual)
- Site estático com Tailwind compilado, JS modularizado, SEO local (`AutoRepair`), Open Graph, acessibilidade básica, dados 100% reais e publicação em CDN gratuita com domínio próprio.

### Fase 2 — Medição e Tração Local (30 a 60 dias pós-lançamento)
- **Google Search Console:** cadastrar domínio, submeter `sitemap.xml` e acompanhar termos de busca locais (*"oficina mecânica Parelheiros"*, *"troca de óleo Parelheiros"*).
- **Analytics leve + eventos de conversão:** ativar Cloudflare Web Analytics (zero cookies) ou GA4 assíncrono rastreando cliques em WhatsApp, rotas do mapa e envio do pré-orçamento.
- **Integração com Google Meu Negócio:** vincular o site no perfil GBP com parâmetro UTM (`?utm_source=gbp&utm_medium=organic`) e criar QR Code físico na oficina incentivando avaliações no Google.
- **Seção de FAQ local e galeria real:** responder dúvidas recorrentes (pagamento, garantia, agendamento, marcas atendidas) e exibir fotos reais da oficina para aumentar confiança e SEO.

### Fase 3 — Autoridade Orgânica e Automação Leve (3 a 6 meses)
- **Páginas dedicadas por serviço / dicas locais:** criar páginas estáticas focadas em buscas de alta intenção (ex.: `/revisao-preventiva-parelheiros`, `/freios-suspensao-parelheiros`, `/diagnostico-scanner-parelheiros`) para ampliar tráfego orgânico sem anúncios pagos.
- **Avaliações reais sincronizadas no build:** caso o volume de avaliações cresça bastante, consumir a Google Places API via script agendado (GitHub Actions semanal) gerando JSON estático no repositório — mantém custo praticamente zero e zero impacto no tempo de carregamento.
- **Pré-agendamento estruturado (sob demanda):** somente se o volume de mensagens no WhatsApp se tornar gargalo operacional, evoluir o modal para seleção de turno (manhã/tarde) enviando notificação para WhatsApp + registro simples em planilha (Google Sheets/webhook), mantendo arquitetura serverless.
