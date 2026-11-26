# Especificação de UX/UI, Mobile-First, Acessibilidade e CRO — Garage Route 66

> **Atualização:** este documento é do plano inicial. A estrutura atual (`src/`, `public/`, `dist/`, build com Tailwind compilado e `client-config.json`) está descrita em [ARCHITECTURE.md](../ARCHITECTURE.md). Onde houver divergência de caminhos (`assets/...`, `index.html` na raiz), vale o ARCHITECTURE.md. Para publicar, o diretório de saída agora é `dist` e o comando de build é `node scripts/build.mjs` (não é mais "sem build").


**Arquivo alvo:** `/home/saprigio/Projetos/garageroute66/index.html`  
**Contexto:** Landing page local para oficina mecânica automotiva em Parelheiros – SP (foco em motoristas acessando pelo celular, muitas vezes com urgência ou buscando confiança rápida antes de chamar no WhatsApp).  
**Restrição de marca:** Preservar integralmente a identidade aprovada — fundo escuro (`#141518` / `#1C1E22`), vermelho Route 66 (`#DC2626`), escudo SVG Route 66 e tipografia `Oswald` (display) + `Inter` (corpo).

---

## Resumo de Prioridades para Implementação

| Prioridade | Frente | Entregas-chave |
| :--- | :--- | :--- |
| **P0 (Agora)** | Mobile-First & Bugs Críticos | Menu mobile acessível, `scroll-mt-24` nas seções, cards de serviço abrindo modal pré-selecionado, bloqueio de scroll + animação real + reset do modal, correção do ícone de erro no toast. |
| **P1 (Agora)** | Conversão (CRO) & WCAG | Link clicável para avaliações reais no Google, selo 5,0 do Hero clicável, status "Aberto/Fechado" também no Hero, ARIA completo no modal e menu, foco visível (`focus-visible`), ajustes de contraste AA e altura mínima de toque (`44px`). |
| **P2 (Conteúdo)** | Prova Social & Fotos Reais | Troca da foto Unsplash por foto real da oficina/fachada (WebP), substituição dos 3 depoimentos genéricos por avaliações reais do Google, inclusão de formas de pagamento e botão "Ligar" na seção Localização. |

---

## 1. Jornada Mobile-First

### 1.1 Header Compacto + Menu Mobile (Drawer/Dropdown Leve)
Hoje, abaixo de `md` (`768px`), `<nav class="hidden md:flex">` some sem alternativa, deixando o usuário mobile sem navegação rápida. Além disso, em telas de `320px–375px`, o logo atual (`w-12` + `text-2xl`) compete espaço com o botão de WhatsApp.

**Especificação do Header Mobile:**
- **Altura:** `h-16 sm:h-20` (`64px` no mobile, `80px` a partir de `sm`).
- **Logo responsivo:**
  - Escudo: `w-10 h-10 sm:w-12 sm:h-12`.
  - Nome: `text-lg sm:text-2xl`.
  - Subtítulo (`Oficina Mecânica • Parelheiros`): `text-[10px] sm:text-[11px]`.
- **Ações à direita:**
  - Botão `Pré-Orçamento`: manter `hidden lg:inline-flex` (no mobile/tablet vai para o menu mobile e Hero).
  - Botão `WhatsApp`: `px-3 py-2.5 sm:px-4 min-h-[44px]` — no mobile exibir ícone + `"WhatsApp"` (`text-xs sm:text-sm`).
  - Botão Menu Mobile (`md:hidden`): `w-11 h-11` (`44x44px`), ícone hambúrguer que alterna para `X` quando aberto.

**Estrutura do Menu Mobile (Dropdown logo abaixo do header):**
- Posição: dentro ou logo abaixo do `<header>`, ocupando `100%` da largura (`bg-garage-dark/98 backdrop-blur-md border-b border-garage-border shadow-2xl`).
- Backdrop clicável atrás do menu (`fixed inset-0 top-16 bg-black/60 z-30 md:hidden`) para fechar tocando fora.
- Itens:
  1. `Serviços` (`#servicos`) — `min-h-[48px] flex items-center px-4`
  2. `Diferenciais` (`#diferenciais`) — `min-h-[48px]`
  3. `Avaliações (5,0 ★)` (`#avaliacoes`) — `min-h-[48px]`
  4. `Localização e Horários` (`#localizacao`) — `min-h-[48px]`
  5. Divisor (`border-t border-garage-border my-2`)
  6. Botão destaque: `Solicitar Pré-Orçamento Rápido` (`w-full min-h-[48px] bg-garage-red text-white font-bold rounded-xl`) — fecha o menu e chama `openQuoteModal()`.
  7. Link secundário: `Ligar (11) 94379-6788` (`tel:+5511943796788`, `w-full min-h-[48px] bg-garage-card border border-garage-border rounded-xl`).
- **Comportamento obrigatório:** fechar automaticamente ao clicar em qualquer link âncora, ao clicar no backdrop, ao pressionar `Escape` ou ao redimensionar para desktop (`>= 768px`).

```html
<!-- Botão no Header (dentro da div de ações, visível apenas < md) -->
<button
    type="button"
    id="mobile-menu-btn"
    aria-expanded="false"
    aria-controls="mobile-menu"
    aria-label="Abrir menu de navegação"
    class="md:hidden inline-flex items-center justify-center w-11 h-11 rounded-xl border border-garage-border bg-garage-card text-white hover:border-slate-500 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-garage-red focus-visible:ring-offset-2 focus-visible:ring-offset-garage-dark"
>
    <!-- Alternar hidden entre ícone menu e ícone X via JS -->
    <svg id="icon-menu-open" class="w-5 h-5" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16"/></svg>
    <svg id="icon-menu-close" class="w-5 h-5 hidden" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
</button>
```

### 1.2 Espaçamentos e Alturas de Toque (Touch Targets)
- **Hero acima da dobra (mobile):** reduzir padding superior/inferior no mobile de `pt-32 pb-20` para `pt-24 pb-14 sm:pt-32 sm:pb-20 lg:pt-40 lg:pb-28`, garantindo que selo 5,0 + título + subtítulo + CTA primário apareçam já no primeiro viewport do celular.
- **Alvos de toque mínimos (`>= 44x44px`):**
  - Botão `"Copiar endereço"` (linha 554): trocar `px-3 py-1.5` (~30px) por `min-h-[44px] px-4 py-2.5`.
  - Botão `X` fechar modal (linha 680): trocar `p-2` (36x36px) por `w-11 h-11 flex items-center justify-center`.
  - Links do rodapé (`@garageroute66_` e `(11) 94379-6788`): garantir `min-h-[44px]`.
  - CTAs de cards, modal e Hero: manter `min-h-[48px]`.
- **Respiro no rodapé para o FAB:** adicionar `pb-24 sm:pb-12` no `<footer>` para evitar que o botão flutuante do WhatsApp tampe o texto de endereço/copyright no celular.

### 1.3 Comportamento do Botão Flutuante do WhatsApp (FAB)
Problemas atuais (linha 661):
1. Aparece simultaneamente no topo da tela junto com o WhatsApp do Header e o CTA principal do Hero (3 botões de WhatsApp na mesma dobra no celular).
2. `gap-3` fica ativo mesmo quando o label está colapsado (`max-w-0`), deixando o ícone ligeiramente deslocado para a direita dentro do círculo.
3. Permanece visível com o modal ou menu mobile abertos.

**Especificação:**
- **Posicionamento seguro (notch/barra gestual iOS/Android):** `fixed bottom-[max(1.25rem,env(safe-area-inset-bottom))] right-4 sm:bottom-6 sm:right-6 z-40`.
- **Centralização correta do ícone:** trocar `gap-3` por `gap-0 md:group-hover:gap-3` e definir `w-14 h-14 md:w-auto md:min-w-[3.5rem] justify-center`.
- **Visibilidade inteligente:**
  - Ocultar no topo inicial enquanto o CTA do Hero estiver visível (`window.scrollY < 260`), exibindo com transição suave (`opacity-100 translate-y-0` vs `opacity-0 translate-y-4 pointer-events-none`) após o usuário começar a rolar.
  - Ocultar imediatamente sempre que o modal de pré-orçamento ou o menu mobile estiver aberto.

---

## 2. Fluxo de Conversão (CRO)

### 2.1 Cards de Serviço → Modal de Pré-Orçamento Pré-Selecionado
**Problema atual:** Os 6 botões `"Orçar este serviço"` (linhas 355–453) abrem o WhatsApp direto sem informar o veículo nem o sintoma. Na prática, o mecânico precisa responder perguntando *"Qual o carro, ano e o que está acontecendo?"*, gerando atrito e queda na conversão.

**Solução (implementar nos 6 cards):**
1. Substituir os `<a href="https://wa.me/...">` dos 6 cards por `<button type="button" onclick="openQuoteModal('NOME_EXATO_DO_SERVICO')">` com o valor exato correspondente às `<option>` do `<select id="service-select">`:
   - `Revisão Preventiva Completa`
   - `Diagnóstico Eletrônico (Scanner)`
   - `Sistema de Freios e Suspensão`
   - `Troca de Óleo e Filtros`
   - `Motor e Injeção Eletrônica`
   - `Arrefecimento e Embreagem`
2. Atualizar `openQuoteModal(preselectedService = '')`:
   - Se `preselectedService` for informado e existir nas opções do `#service-select`, selecionar automaticamente essa opção.
   - Caso contrário, manter a opção padrão (`Revisão Preventiva Completa` ou `Outro serviço / Avaliação geral`).
   - Focar automaticamente no input `#car-model` para o usuário digitar só o carro e enviar em 10 segundos.
3. **Microcopy na seção Serviços (linha 335):**
   - Atualizar subtítulo para: *"Escolha o serviço abaixo, informe o modelo do seu carro e envie o pré-orçamento pronto pelo WhatsApp."*
4. **Reforço de baixa fricção dentro do Modal:**
   - Abaixo dos botões de ação do formulário, adicionar nota curta (`text-xs text-slate-400 text-center mt-2`):  
     *"Sem compromisso • Você continua a conversa direto com o mecânico no WhatsApp."*
   - Opcionalmente, adicionar `<p id="quote-modal-desc" class="text-xs text-slate-400 mt-1">Preencha em 15 segundos para receber uma resposta mais rápida.</p>` abaixo do título do modal.

### 2.2 Otimização de CTAs e Sinais de Confiança
- **Selo Google 5,0 no Hero (linha 107):** transformar de `<div>` em `<a href="#avaliacoes">` com hover sutil (`hover:border-amber-400/50 transition-colors`), permitindo ao visitante saltar direto para as provas sociais.
- **Status "Aberto agora / Fechado" visível já no Hero:**
  - Hoje o badge dinâmico (`#open-status-badge`) só existe na última seção (`#localizacao`).
  - Trocar a seleção por classe (`.js-open-status`) e renderizar um badge compacto também no bloco de horários da barra rápida do Hero (linha 157). Motorista com pane ou barulho no carro decide em segundos ao ver `● Aberto agora`.
- **Link clicável para Avaliações Reais no Google (seção `#avaliacoes`, linha 234):**
  - Adicionar dentro do card `5,0 Google` (ou logo abaixo do grid de depoimentos) um link explícito de verificação:
    ```html
    <a
        href="https://www.google.com/maps/search/?api=1&query=Garage+Route+66+Rua+Bem+Te+Vi+32+Parelheiros+Sao+Paulo"
        target="_blank"
        rel="noopener noreferrer"
        class="inline-flex items-center gap-1.5 text-xs font-semibold text-amber-400 hover:text-amber-300 underline underline-offset-4 mt-2 min-h-[36px]"
    >
        <span>Ver todas as 43 avaliações no Google</span>
        <svg class="w-3.5 h-3.5" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
    </a>
    ```
  - *Nota:* Assim que tiver o link curto oficial do Google Perfil da Empresa (`g.page/r/...`), substituir a URL de busca acima pela URL direta da aba de avaliações.
- **Seção Localização (linhas 589–599):**
  - Simplificar texto do botão WhatsApp para não quebrar feio em telas de `360px`: `"WhatsApp • (11) 94379-6788"`.
  - Adicionar botão secundário `"Ligar agora: (11) 94379-6788"` (`href="tel:+5511943796788"`) ao lado ou abaixo de "Traçar Rota" — em emergências mecânicas, ligação direta ainda converte muito bem no mobile.

---

## 3. Correções de UX & Bugs Visuais

### 3.1 `scroll-mt` nas Seções (Compensação do Header Fixo)
O header tem `h-16 sm:h-20` (`64px` / `80px`). Sem `scroll-margin-top`, os links âncora escondem o topo da seção atrás do header.
- Adicionar `scroll-mt-20 sm:scroll-mt-24` em:
  - `<section id="avaliacoes" ...>` (linha 218)
  - `<section id="servicos" ...>` (linha 327)
  - `<section id="diferenciais" ...>` (linha 461)
  - `<section id="localizacao" ...>` (linha 529)

### 3.2 Animação Real do Modal (Fade + Scale) + Scroll Lock + Altura Mobile
**Bugs atuais:**
- Linha 670 usa `animate-[fadeIn_0.2s_ease-out]`, mas `@keyframes fadeIn` não foi definido — o modal abre sem animação.
- O fundo (`<body>`) continua rolando atrás do modal.
- Em celulares com teclado virtual aberto, o modal não tem rolagem interna (`max-h-[90dvh] overflow-y-auto`), podendo esconder o botão de envio.

**Especificação pronta para o Dev Full:**
- **Backdrop (`#quote-modal`):**
  - Classes base: `fixed inset-0 z-50 hidden items-center justify-center p-4 bg-black/80 backdrop-blur-sm opacity-0 transition-opacity duration-200 motion-reduce:transition-none`
- **Painel interno (`#quote-modal-panel`):**
  - Remover `animate-[fadeIn_0.2s_ease-out]`.
  - Adicionar: `max-h-[90dvh] overflow-y-auto overscroll-contain transform scale-95 translate-y-2 opacity-0 transition-all duration-200 ease-out motion-reduce:transition-none`
- **Abertura (`openQuoteModal`):**
  1. Salvar `lastFocusedElement = document.activeElement`.
  2. Pré-selecionar `#service-select` se parâmetro for passado.
  3. Travar scroll do fundo: `document.body.classList.add('overflow-hidden')`.
  4. Remover `hidden`, adicionar `flex`.
  5. No próximo `requestAnimationFrame`: trocar `opacity-0` → `opacity-100` no backdrop, e no painel trocar `scale-95 translate-y-2 opacity-0` → `scale-100 translate-y-0 opacity-100`.
  6. Focar `#car-model` (com `{ preventScroll: true }`).
- **Fechamento (`closeQuoteModal`):**
  1. Reverter classes de transição (`opacity-100` → `opacity-0` no backdrop; `scale-100 translate-y-0 opacity-100` → `scale-95 translate-y-2 opacity-0` no painel).
  2. Após `200ms` (ou imediato se `prefers-reduced-motion`): adicionar `hidden`, remover `flex` e remover `overflow-hidden` do `<body>`.
  3. Devolver foco para `lastFocusedElement?.focus()`.

### 3.3 Reset do Formulário Após Envio
Em `sendWhatsAppQuote(event)` (linhas 796–821):
- Após montar a `whatsappUrl` e abrir o WhatsApp, executar:
  ```js
  document.getElementById('quote-form').reset();
  ```
- Isso evita que dados antigos de um veículo/sintoma fiquem presos caso o usuário abra o modal novamente.

### 3.4 Toast com Feedback Visual e Semântico Correto
**Bugs atuais (linhas 44 e 749–765):**
- `showToast(msg, 'error')` mostra fundo vermelho mas mantém o **ícone de checkmark (✓)**!
- Container `fixed top-24 right-4` pode vazar horizontalmente em telas de `320px–360px`.
- Usa `innerHTML` direto com `${message}`.

**Correções:**
- Container `#toast-box`:
  ```html
  <div id="toast-box" aria-live="polite" aria-atomic="true" class="fixed top-20 sm:top-24 inset-x-4 sm:inset-x-auto sm:right-4 sm:max-w-sm z-[60] flex flex-col gap-2 pointer-events-none"></div>
  ```
- Ícone condicional por `type`:
  - `success`: fundo `bg-emerald-700 border border-emerald-500/40` + ícone check (`M5 13l4 4L19 7`).
  - `error`: fundo `bg-garage-red border border-red-400/40` + ícone alerta (`M12 9v2m0 4h.01M10.29 3.86l-7.5 13A1 1 0 003.65 18h16.7a1 1 0 00.86-1.5l-7.5-13a1 1 0 00-1.72 0z`) + `role="alert"`.
- Inserir o texto via `span.textContent = message` (mais seguro) e animar entrada (`opacity-0 -translate-y-2` → `opacity-100 translate-y-0`).

### 3.5 Ajustes Adicionais Rápidos
- **`copyAddress()` (linhas 824–837):** priorizar `navigator.clipboard?.writeText(addressText)` com fallback invisível (`textarea.style.cssText = 'position:fixed;opacity:0;pointer-events:none'`) para não provocar salto de scroll no celular.
- **Ano do rodapé (linha 654):** atualizar `© 2025` para ano dinâmico via `<span id="current-year">2026</span>` preenchido por `new Date().getFullYear()`.
- **Escudo Route 66 do rodapé (linhas 625–628):** padronizar com o mesmo SVG completo do header (incluindo a faixa `ROUTE`) para consistência visual da marca.

---

## 4. Acessibilidade (WCAG 2.1 Básico — Nível A/AA)

### 4.1 Estrutura Semântica e Skip Link
- Adicionar **Skip Link** como primeiro filho do `<body>`:
  ```html
  <a href="#conteudo-principal" class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[70] focus:px-4 focus:py-2.5 focus:rounded-xl focus:bg-garage-red focus:text-white focus:font-bold focus:shadow-lg">
      Pular para o conteúdo principal
  </a>
  ```
- Envolver todas as `<section>` entre `<header>` e `<footer>` dentro de `<main id="conteudo-principal">`.
- Nomear as navegações: `<nav aria-label="Navegação principal">` (desktop) e `<nav id="mobile-menu" aria-label="Menu mobile">` (mobile).

### 4.2 Atributos ARIA e Teclado no Modal
- No container `#quote-modal`:
  ```html
  <div
      id="quote-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="quote-modal-title"
      aria-describedby="quote-modal-desc"
      class="..."
  >
  ```
- Adicionar `id="quote-modal-title"` no `<h3>Solicitar Pré-Orçamento</h3>` e `id="quote-modal-desc"` no parágrafo explicativo curto logo abaixo.
- **Focus Trap (Tab / Shift+Tab):** enquanto o modal estiver aberto, interceptar `Tab` para ciclar apenas entre os elementos focáveis internos (`button, input, select, textarea, [href], [tabindex]:not([tabindex="-1"])`), evitando que o usuário navegue "por trás" do overlay.
- Manter fechamento com `Escape` e clique no backdrop.

### 4.3 Foco Visível (`focus-visible`)
- **Remover** `focus:outline-none` sem substituto no logo (linha 52) e `outline-none` isolado nos inputs (linhas 695, 705, 725).
- Padronizar anel de foco visível apenas para navegação por teclado (`focus-visible`):
  - **Botões e links:** `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-garage-red focus-visible:ring-offset-2 focus-visible:ring-offset-garage-dark`
  - **Campos de formulário (`input`, `select`, `textarea`):** `focus:outline-none focus-visible:border-garage-red focus-visible:ring-2 focus-visible:ring-garage-red/40`
- Atalho limpo: pode ser aplicado via CSS customizado em `<style>` no `<head>` para cobrir todos os elementos interativos (`a, button, input, select, textarea`) com consistência.

### 4.4 `alt`, SVGs Decorativos e Leitores de Tela
- Adicionar `aria-hidden="true"` em todos os ícones SVG decorativos (ícones de WhatsApp junto a texto, setas, escudo ao lado do nome da oficina, ícones dos cards de serviço e diferenciais).
- Estrelas de avaliação (`★★★★★`): aplicar `aria-label="Avaliação 5 de 5 estrelas"` no elemento pai e `aria-hidden="true"` nos SVGs/caracteres de estrela, evitando repetição verbal em leitores de tela.
- `alt` da imagem principal do Hero: manter descritivo e fiel à foto exibida (ex.: *"Fachada da oficina mecânica Garage Route 66 em Parelheiros com área de atendimento organizada"* quando a foto real entrar).

### 4.5 Correções de Contraste (WCAG AA >= 4.5:1)
Auditoria nos pares cor/fundo atuais de `index.html`:

| Elemento / Linha | Atual | Problema | Substituição recomendada |
| :--- | :--- | :--- | :--- |
| "Domingo" (L580) e rodapé (L653) | `text-slate-500` sobre `#1C1E22` / `#0F1012` | ~3.6:1 (falha AA em texto pequeno) | `text-slate-400` (~6.5:1+) |
| Labels pequenos (`text-xs`) em vermelho (L224, L330, L466, L532, L548, L582, L677) | `text-garage-red` (`#DC2626`) sobre `#141518` / `#1C1E22` | ~3.7:1 em 12px (falha AA 4.5:1) | `text-red-400` (`#F87171`, ~6.8:1) ou `text-red-500` (`#EF4444`, ~4.5:1) — manter `#DC2626` em botões, bordas e títulos grandes |
| Placeholders do modal (L695, L725) | `placeholder-slate-500` sobre `#141518` | ~3.9:1 | `placeholder-slate-400` |
| Botões WhatsApp (L85, L595, L661, L733) | `bg-emerald-600` (`#059669`) + `text-white` | ~3.76:1 em `text-sm` (abaixo de 4.5:1) | `bg-emerald-700 hover:bg-emerald-600` (`#047857` + branco = ~5.5:1, passa AA com folga) |

---

## 5. Recomendações de Conteúdo Real (Confiança Local)

Em oficina mecânica de bairro, **autenticidade vende mais que estética genérica**. Dois elementos atuais reduzem a credibilidade se um morador de Parelheiros analisar com atenção:

### 5.1 Substituir Foto Stock do Hero por Foto Real da Oficina
- **Situação atual:** linha 182 carrega foto genérica do Unsplash (`photo-1619642751034-765dfdf7c58e`).
- **Ação recomendada:** fotografar a oficina real e hospedar localmente em `/assets/img/` (ex: `fachada-garage-route-66.webp` ou `oficina-garage-route-66.webp`):
  - **Opção principal (Hero):** fachada limpa da Rua Bem Te Vi, 32 mostrando a identidade Route 66 ou interior organizado com carro no elevador e mecânico uniformizado.
  - **Especificação técnica da imagem:** formato `WebP` (fallback `JPG`), proporção `4:3` ou `16:10`, largura máxima `960px`, peso alvo `< 140 KB`, atributos `width="900" height="600"` e `fetchpriority="high"` (já que está acima da dobra no desktop).
  - **Enquanto a foto real não chega:** manter a atual apenas como provisória, mas remover do `alt` a afirmação de que a foto foi tirada dentro da Garage Route 66 (usar `"Diagnóstico automotivo especializado — serviços da Garage Route 66"`).

### 5.2 Substituir os 3 Depoimentos Genéricos por Avaliações Reais do Google
- **Situação atual:** os depoimentos de *"Rodrigo Carvalho"*, *"Fernanda Souza"* e *"Marcelo Almeida"* (linhas 256–322) são ilustrativos, mas carregam o rótulo `"Avaliação verificada • Google"`. Se o cliente clicar no Google e não encontrar esses nomes, perde confiança na hora.
- **Ação recomendada:**
  1. Copiar **3 avaliações reais de 5 estrelas** do perfil da Garage Route 66 no Google Maps (priorizando menções a honestidade, preço justo, clareza no diagnóstico e prazo).
  2. Exibir o nome real como aparece no Google (ou Primeiro Nome + inicial do sobrenome), a data relativa (ex.: `"Avaliação real no Google"`) e manter o link `"Ver todas as 43 avaliações no Google"` logo acima ou abaixo.
  3. Deixar um comentário no HTML (`<!-- Atualizar periodicamente com a contagem real do Google Perfil da Empresa -->`) próximo ao número `43` para facilitar manutenção.

### 5.3 Pequenos Ganhos de Confiança Local (Opcional / P2)
- **Formas de pagamento:** incluir uma linha discreta na seção de Diferenciais ou Localização (ex.: *"Aceitamos Pix, débito e cartão de crédito — consulte parcelamento"*), validando antes com o proprietário.
- **Referência de localização:** se houver ponto de referência conhecido em Parelheiros próximo à Rua Bem Te Vi, 32, adicionar abaixo do CEP para facilitar quem está dirigindo na região.
