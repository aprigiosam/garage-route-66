# Infraestrutura e Deploy — Garage Route 66

> **Atualização:** este documento é do plano inicial. A estrutura atual (`src/`, `public/`, `dist/`, build com Tailwind compilado e `client-config.json`) está descrita em [ARCHITECTURE.md](../ARCHITECTURE.md). Onde houver divergência de caminhos (`assets/...`, `index.html` na raiz), vale o ARCHITECTURE.md. Para publicar, o diretório de saída agora é `dist` e o comando de build é `node scripts/build.mjs` (não é mais "sem build").


Guia objetivo de hospedagem, domínio `.com.br`, segurança e publicação do site estático da **Garage Route 66** (Oficina Mecânica em Parelheiros - SP).

---

## 1. Recomendação de Hospedagem Gratuita

### Escolha principal recomendada: **Cloudflare Pages**

Para o site institucional da Garage Route 66, a **Cloudflare Pages** é a melhor opção de custo-benefício (custo **R$ 0/mês**):

- **Uso comercial permitido no plano gratuito** (diferente do plano Hobby da Vercel, que nos termos de uso é voltado a projetos pessoais/não comerciais).
- **Largura de banda ilimitada** (sem susto de cobrança se um post no Instagram ou anúncio viralizar).
- **CDN global com presença forte em São Paulo**, garantindo carregamento muito rápido para clientes em Parelheiros e região metropolitana.
- **HTTPS (SSL) automático e gratuito** com renovação sem intervenção manual.
- **Suporte nativo ao arquivo `_headers`** já configurado neste repositório.
- **Deploy descomplicado**, tanto via GitHub (automático a cada `git push`) quanto por upload direto da pasta.

### Comparativo rápido

| Plataforma | Custo | Uso Comercial no Plano Grátis | SSL + CDN Global | Arquivo de Config Pronto | Indicação |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cloudflare Pages** | **Grátis** | **Sim** | Sim (PoPs em SP) | `_headers` | **Recomendada (#1)** |
| **Vercel** | Grátis (Hobby) / Pago (Pro) | Restrito no Hobby | Sim | `vercel.json` | Boa alternativa técnica |
| **Netlify** | Grátis (com limite de banda) | Sim | Sim | `_headers` | Boa alternativa |
| **GitHub Pages** | Grátis | Sim (repo público) | Sim | Não suporta `_headers` | Mais simples, menos controle de headers |

---

## 2. Arquivos de Infraestrutura Criados

| Arquivo | Função |
| :--- | :--- |
| `.gitignore` | Evita subir arquivos temporários de sistema, IDE, Node e segredos para o Git. |
| `robots.txt` | Libera indexação no Google, bloqueia `/docs/` e aponta o endereço do `sitemap.xml`. |
| `sitemap.xml` | Mapa de URLs para os buscadores (usando `https://garageroute66.com.br/` como placeholder). |
| `_headers` | Headers de segurança (HSTS, CSP, X-Frame-Options, Referrer-Policy, Permissions-Policy) e cache otimizado para **Cloudflare Pages** e **Netlify**. |
| `vercel.json` | Mesmas regras de segurança, cache e *Clean URLs* caso optem por publicar na **Vercel**. |

> **Nota sobre a Content-Security-Policy (CSP):**
> A CSP configurada em `_headers` e `vercel.json` foi calibrada para proteger o site **sem quebrar** o iframe do Google Maps (`google.com/maps`), Google Fonts (`fonts.googleapis.com` / `fonts.gstatic.com`), Tailwind CDN (`cdn.tailwindcss.com`), scripts inline ou imagens externas (`images.unsplash.com` / `placehold.co`).
> Se no futuro o Tailwind CDN for substituído por CSS compilado localmente e os scripts inline forem movidos para arquivos `.js` externos, você poderá remover `'unsafe-inline'`, `'unsafe-eval'` e `https://cdn.tailwindcss.com` da diretiva `script-src`.

---

## 3. Passo a Passo para Publicar

### Opção A — Deploy contínuo via GitHub + Cloudflare Pages (Recomendado)

Com este fluxo, toda vez que você alterar o site e der `git push`, o site em produção é atualizado automaticamente em menos de 1 minuto.

#### 1. Subir o projeto para o GitHub
No diretório do projeto (`/home/saprigio/Projetos/garageroute66`):

```bash
git init
git add .
git commit -m "Estrutura inicial do site e infraestrutura Garage Route 66"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/garageroute66.git
git push -u origin main
```

#### 2. Conectar na Cloudflare Pages
1. Crie ou acesse sua conta gratuita em [dash.cloudflare.com](https://dash.cloudflare.com).
2. No menu lateral, acesse **Workers & Pages** → **Create** → aba **Pages** → **Connect to Git**.
3. Autorize o GitHub e selecione o repositório `garageroute66`.
4. Configure o build (site estático puro, sem etapa de compilação):
   - **Project name:** `garageroute66`
   - **Production branch:** `main`
   - **Framework preset:** `None`
   - **Build command:** `node scripts/build.mjs` (rode `npm install` antes; no Cloudflare use `npm install && node scripts/build.mjs`)
   - **Build output directory:** `dist`
5. Clique em **Save and Deploy**.
6. Em ~30 segundos o site estará no ar em `https://garageroute66.pages.dev` com HTTPS ativo.

---

### Opção B — Upload Direto na Cloudflare Pages (Sem precisar de GitHub)

Ideal se quiser colocar o site no ar em 2 minutos sem usar Git:

1. Acesse [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create** → **Pages** → **Upload assets**.
2. Dê o nome `garageroute66` e clique em **Create project**.
3. Arraste a pasta do projeto (contendo `index.html`, `_headers`, `robots.txt`, `sitemap.xml` e eventuais imagens) para a área de upload.
   - *Dica:* não precisa enviar pastas ocultas como `.git/`.
4. Clique em **Deploy site**.

---

### Opção C — Publicar na Vercel (Alternativa)

O projeto já possui `vercel.json` pronto.

- **Via Painel Web:** acesse [vercel.com](https://vercel.com), clique em **Add New → Project**, importe o repositório do GitHub e clique em **Deploy** (sem comando de build).
- **Via Terminal (CLI):**
  ```bash
  npx vercel --prod
  ```

---

## 4. Registro e Apontamento de Domínio `.com.br` (Registro.br)

O único custo recorrente recomendado para profissionalizar a oficina é o domínio `.com.br` (~R$ 40/ano direto no órgão oficial).

### Passo 1: Registrar o domínio
1. Acesse [registro.br](https://registro.br) e pesquise o domínio desejado (ex.: `garageroute66.com.br`).
2. Faça o cadastro com CPF ou CNPJ da oficina e conclua o pagamento anual.

### Passo 2: Apontar para a Cloudflare (Jeito mais simples e seguro)
Usar o DNS gratuito da Cloudflare junto com o Cloudflare Pages ativa HTTPS automático, CDN e redirecionamento de `www` sem dor de cabeça:

1. No painel da **Cloudflare**, clique em **Add a site** (Adicionar site), digite `garageroute66.com.br` e escolha o plano **Free**.
2. A Cloudflare vai exibir **2 servidores DNS (Nameservers)**, parecidos com:
   - `ana.ns.cloudflare.com`
   - `bob.ns.cloudflare.com`
3. Acesse o painel do **Registro.br** → clique no domínio `garageroute66.com.br` → seção **DNS** → clique em **Alterar servidores DNS**.
4. Cole os 2 Nameservers fornecidos pela Cloudflare e clique em **Salvar dados**.
5. Aguarde a propagação (normalmente de 15 minutos a 2 horas; prazo máximo de 24h).

### Passo 3: Vincular o domínio ao projeto no Cloudflare Pages
1. No painel da Cloudflare, abra **Workers & Pages** → projeto `garageroute66` → aba **Custom domains**.
2. Clique em **Set up a custom domain**, digite `garageroute66.com.br` e confirme (a Cloudflare cria o registro DNS e o certificado SSL automaticamente).
3. Repita o processo adicionando `www.garageroute66.com.br` (ou crie uma *Redirect Rule* de `www.garageroute66.com.br/*` para `https://garageroute66.com.br/$1` com status `301` para evitar conteúdo duplicado no Google).

### Alternativa: Se publicar na Vercel mantendo o DNS no Registro.br
No painel do Registro.br → **DNS** → **Editar Zona**, adicione:
- Registro `A`: nome em branco (`@`) → valor `76.76.21.21`
- Registro `CNAME`: nome `www` → valor `cname.vercel-dns.com`

### Passo 4: Conferir o domínio nos arquivos de SEO
Se o domínio registrado for diferente de `garageroute66.com.br`, atualize a URL em:
- `robots.txt` (linha `Sitemap:`)
- `sitemap.xml` (tag `<loc>`)
- E, no `index.html`, quaisquer tags `<link rel="canonical">` e `og:url` / `og:image` que forem adicionadas.

---

## 5. Fluxo de Atualização no Dia a Dia

Com GitHub + Cloudflare Pages conectados, atualizar textos, telefone, horários ou fotos leva poucos segundos:

```bash
# 1. Edite os arquivos localmente e confira no navegador
# 2. Envie a alteração
git status
git add .
git commit -m "Atualiza serviços e horários de atendimento"
git push
```

A Cloudflare detecta o push, publica a nova versão automaticamente e mantém histórico de deploys anteriores (permitindo *rollback* em 1 clique caso algo saia errado).

---

## 6. Checklist Pós-Deploy

Execute esta verificação assim que o domínio estiver no ar com HTTPS:

### A. Validação Técnica e Funcional
- [ ] Abrir `https://garageroute66.com.br` e confirmar cadeado HTTPS válido (sem avisos de conteúdo misto).
- [ ] Testar se `http://garageroute66.com.br` e `https://www.garageroute66.com.br` redirecionam corretamente para `https://garageroute66.com.br`.
- [ ] Verificar se o **iframe do Google Maps** carrega normalmente na seção de localização.
- [ ] Testar o carregamento das fontes (**Oswald** e **Inter**) e das imagens.
- [ ] Testar os botões de **WhatsApp** e o modal de **Pré-Orçamento** no celular e no computador.
- [ ] Abrir `/robots.txt` e `/sitemap.xml` no navegador para confirmar que retornam HTTP `200`.
- [ ] Conferir os headers de segurança em [securityheaders.com](https://securityheaders.com) (ou via `curl -I https://garageroute66.com.br`).

### B. Google Search Console (Indexação no Google)
- [ ] Acessar [search.google.com/search-console](https://search.google.com/search-console) e adicionar a propriedade do tipo **Domínio** (`garageroute66.com.br`).
- [ ] Verificar a propriedade via registro `TXT` no DNS (se estiver na Cloudflare, a verificação é automática em poucos cliques).
- [ ] No menu **Sitemaps**, enviar `https://garageroute66.com.br/sitemap.xml`.
- [ ] Usar **Inspeção de URL** na página inicial (`https://garageroute66.com.br/`) e clicar em **Solicitar indexação**.

### C. Google Meu Negócio (Perfil da Empresa no Google)
- [ ] Acessar o perfil da **Garage Route 66** no Google (Google Maps / Perfil da Empresa).
- [ ] Atualizar o campo **Website** com `https://garageroute66.com.br`.
- [ ] Confirmar que **endereço** (`Rua Bem Te Vi, 32 - Parelheiros, São Paulo - SP, 04896-310`), **telefone/WhatsApp** e **horário de funcionamento** estão 100% idênticos aos exibidos no site (consistência NAP melhora o ranqueamento local).

### D. Performance (PageSpeed Insights)
- [ ] Rodar o teste em [pagespeed.web.dev](https://pagespeed.web.dev) para a URL final.
- [ ] Verificar pontuações de **Desempenho, Acessibilidade, Práticas Recomendadas e SEO** no **Mobile** (prioridade, já que a maioria dos motoristas busca pelo celular) e no **Desktop**.
- [ ] *Dica futura:* caso queira elevar ainda mais a nota mobile, trocar imagens externas grandes por arquivos `.webp` locais otimizados e compilar o CSS do Tailwind em produção.

### E. Teste de Preview no WhatsApp (Open Graph)
- [ ] Enviar o link `https://garageroute66.com.br` em uma conversa teste no **WhatsApp** (celular e WhatsApp Web).
- [ ] Confirmar se título, descrição e imagem de prévia aparecem corretamente e sem cortes.
- [ ] Caso o preview apareça sem imagem ou desatualizado, validar as meta tags `og:title`, `og:description`, `og:image` (com URL absoluta HTTPS e tamanho recomendado `1200x630px`) usando [opengraph.xyz](https://www.opengraph.xyz/) ou o [Meta Sharing Debugger](https://developers.facebook.com/tools/debug/).
