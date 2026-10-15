# Parecer de infraestrutura: onde rodar o Garage Route 66

- **Autor:** agente `infra`
- **Data:** 15/10/2026
- **Fase:** decisão. Nenhum recurso foi criado e nenhum código foi alterado.
- **Fronteira:** deploy, backup testado e monitoramento ficam com o `sre`. A LGPD em detalhe fica com `seguranca`. Aqui trato só de onde o sistema roda, de rede, DNS/HTTPS, IaC e custo.

## 1. Recomendação

**Uma instância Amazon Lightsail na região São Paulo (`sa-east-1`) roda app + banco em Docker Compose, com Caddy fazendo o HTTPS automático. O provisionamento é feito com Terraform. Na oficina fica só o navegador.**

- **Tamanho:** bundle Linux de 2 GB com IPv4 incluso, US$ 12/mês, **≈ R$ 62/mês**. Se a stack final for leve, o bundle de 1 GB custa US$ 7, ≈ R$ 36. Com domínio .com.br e snapshots automáticos, o total fica em **≈ R$ 70–85/mês**.
- **Banco:** fica no mesmo host, sem banco gerenciado. A carga é de 1 usuária e poucas OS por dia. Wesley é DBA e opera um MySQL/Postgres em container sem dificuldade. O RDS custaria +R$ 150/mês e o Lightsail DB +R$ 78/mês sem ganho real nessa escala. Esta escolha só se sustenta se o `sre` garantir um dump diário off-site (S3) com restore testado.
- **Por que AWS e não uma VPS mais barata:** é a única opção avaliada que reúne quatro coisas.
  1. Região em São Paulo, com latência de um dígito a poucas dezenas de ms a partir de Parelheiros.
  2. Preço fixo e baixo.
  3. Snapshots nativos.
  4. Domínio total do Wesley: IAM, Terraform, CloudWatch e Route 53. Manutenção remota por quem já opera AWS custa menos horas do que aprender um painel novo.
- **Alternativa equivalente em reais:** Magalu Cloud BV1-1-10, ≈ R$ 35/mês com impostos e região em SP. Vale se faturar em R$ sem IOF for prioridade. A contrapartida é um ecossistema e um provider Terraform menos maduros.
- **Notebook local como servidor: não recomendado**, salvo se a medição da internet (premissa P1) mostrar que a conexão da oficina é inutilizável. Nesse caso ele vira o servidor, com backup off-site obrigatório.
- **Híbrido (nuvem + modo offline): não recomendado na V1.** O custo de sincronização e de resolução de conflitos não se paga para 1 usuária. Para quedas de internet, o plano B é físico (seção 5): hotspot 4G e formulário de papel de contingência.

## 2. Cotação e premissas de preço

- **Câmbio:** PTAX de venda de 13/10/2026: **US$ 1 = R$ 5,0096** e **€ 1 = R$ 5,6092**.
- **Câmbio efetivo usado nas contas:** compra em cartão internacional sofre IOF de 3,5%, então uso **US$ 1 ≈ R$ 5,19** e **€ 1 ≈ R$ 5,81**. O spread do cartão não está incluído.
- **AWS Brasil:** para conta brasileira, a AWS pode faturar em R$ pela AWS Serviços Brasil, com tributos locais no lugar do IOF. Trate os valores da AWS como estimativa de ±10%.
- **Mês:** 730 h para EC2/RDS. O Lightsail cobra por bundle mensal, com teto de 744 h.
- **Fonte dos preços AWS:** Price List API pública de `sa-east-1`, efetiva em set–out/2026. Os bundles do Lightsail em São Paulo têm o mesmo preço da tabela dos EUA. A franquia de transferência é metade da dos EUA, o que é irrelevante aqui.

## 3. Tabela comparativa

Latência estimada até a oficina (RTT): SP ≈ 5–30 ms, EUA Leste ≈ 120–150 ms, EUA Oeste e Europa ≈ 180–250 ms. O valor real depende do provedor local de Parelheiros.

| Opção | Custo mensal (R$) | Região / latência | Se a internet da oficina cair | Se o notebook quebrar ou for roubado | Domínio / DNS / HTTPS | Acesso remoto do Wesley | Provisionamento (IaC) | Lock-in |
|---|---|---|---|---|---|---|---|---|
| **1. Notebook local** (app + banco no notebook) | **≈ 0** de infra. Opcional: Tailscale grátis, S3 para backup ≈ R$ 1 | Local, 0 ms | **Sistema continua funcionando.** Só o backup e o acesso remoto param. | **Perde tudo desde o último backup off-site.** Roubo com disco sem criptografia = incidente LGPD. Volta só depois de comprar e reinstalar outra máquina (dias). | Desnecessário dentro da LAN. Para acesso externo: Cloudflare Tunnel grátis + domínio | Tailscale (SSH/HTTP) + RustDesk/AnyDesk. Depende de o notebook estar ligado e online. | Ansible ou script de bootstrap. Windows complica: precisaria de WSL/Docker Desktop ou Linux dedicado. | Nenhum |
| **2a. Magalu Cloud** BV1-1-10 (1 vCPU / 1 GB / 10 GB) | **≈ 35**, em R$ com impostos (a confirmar na calculadora) | SP (br-se1), baixa | Sistema indisponível na oficina, mas acessível do celular via 4G | Nada se perde: troca o notebook, abre o navegador e volta a operar | Domínio .com.br + DNS (registro.br ou Cloudflare grátis) + Caddy/Let's Encrypt | SSH | Provider Terraform existe, menos maduro. CLI própria. | Baixo (VM + Docker) |
| **2b. Hostinger** VPS KVM 1 (1 vCPU / 4 GB / 50 GB) | **≈ 28** na promoção de 24 meses, **≈ 48** na renovação | SP **incerto** (fonte de abr/2026 diz que SP saiu da lista de VPS). Se for EUA/Europa, alta. | Idem 2a | Idem 2a | Idem 2a | SSH + painel | Sem Terraform oficial relevante: manual + cloud-init | Baixo, mas exige contrato longo |
| **2c. Oracle Always Free** (Ampere A1) | **0** | SP e Vinhedo, baixa | Idem 2a | Idem 2a | Idem 2a | SSH | Terraform OCI maduro | Baixo |
| **2d. Hetzner** (CX/CPX) | ≈ 25–35 (€ 4–6 após os reajustes de abr e jun/2026) | **Sem região na América do Sul**: Europa/EUA, alta | Idem 2a | Idem 2a | Idem 2a | SSH | Terraform excelente | Baixo |
| **2e. DigitalOcean** (droplet de US$ 4–6) | ≈ 21–31. Com MySQL gerenciado: +US$ 15,15 ≈ +79 | **Sem região na América do Sul**: NYC, alta | Idem 2a | Idem 2a | Idem 2a | SSH | Terraform excelente | Baixo |
| **2f. Contabo** Cloud VPS 4 (4 vCPU / 8 GB) | ≈ 26–32 (€ 4,40–5,50, contrato de 24 meses) | Brasil não confirmado. EUA/Europa, alta. | Idem 2a | Idem 2a | Idem 2a | SSH | Manual / API | Baixo |
| **3a. Render** (Starter US$ 7 + Postgres Basic-256mb US$ 6 + storage) | **≈ 69** | Sem SA: Virginia/Ohio, alta | Idem 2a | Idem 2a | Domínio próprio + HTTPS automático | Painel/CLI, sem SSH real | `render.yaml` (Blueprint) | **Médio.** Só Postgres gerenciado, sem MySQL. Dados nos EUA. |
| **3b. Railway** (Hobby US$ 5 + uso; app + MySQL em volume) | **≈ 26–80**, variável conforme RAM | Sem SA (EUA/EU/SG), alta | Idem 2a | Idem 2a | Domínio próprio + HTTPS automático | Painel/CLI | `railway.json` | Médio. Custo por uso, menos previsível. |
| **3c. Fly.io** (gru: app de 512 MB + banco em máquina de 1 GB com volume) | ≈ 95 (estimativa com o markup de ≈1,6× da região gru). Com Managed Postgres: +US$ 38 ≈ +197 | **SP (gru)**, baixa | Idem 2a | Idem 2a | Certificado automático | `fly ssh console` | `fly.toml` | Médio |
| **4a. AWS Lightsail SP**, 2 GB, app + banco no host ✅ | **≈ 62**. Com 1 GB: ≈ 36. Snapshots ≈ 5–16 | SP, baixa | Idem 2a | Idem 2a | Route 53 (zona US$ 0,50 ≈ R$ 2,60) ou registro.br. Caddy/Let's Encrypt. IP estático grátis enquanto anexado. | SSH (chave), browser SSH do console, Tailscale opcional | **Terraform** (`aws_lightsail_*`) + cloud-init | Baixo (VM + Docker) |
| **4b. AWS Lightsail SP** + Lightsail Managed DB 1 GB | ≈ 62 + 78 = **≈ 140** | SP, baixa | Idem | Idem | Idem | Idem | Terraform | Baixo |
| **4c. AWS EC2 t4g.micro + RDS db.t4g.micro** (Single-AZ, 20 GB gp2) | EC2 US$ 9,78 + IPv4 US$ 3,65 + EBS US$ 3,04 + RDS US$ 24,82 + storage US$ 4,38 ≈ US$ 45,7 → **≈ 237**. Com t4g.small: ≈ 288 | SP, baixa | Idem | Idem | Route 53 + ACM/Caddy | SSM Session Manager, sem porta 22 aberta | Terraform | Baixo |

Custos comuns a todas as opções de nuvem:

- **Domínio .com.br:** R$ 40/ano no registro.br, ≈ R$ 3,33/mês. DNS grátis no registro.br ou no Cloudflare.
- **Backup off-site em S3:** < R$ 2/mês para esse volume de dados.

## 4. Análise por critério

**Internet da oficina.** Esse é o fator decisivo, e hoje ninguém conhece a qualidade dela.

- O sistema consome pouquíssima banda. É formulário e JSON: o primeiro carregamento do bundle tem algumas centenas de KB, que ficam em cache, e cada operação depois disso consome poucos KB. Até um 4G fraco dá conta.
- O que mata a experiência é **indisponibilidade**, não latência. Por isso a premissa P1, medir antes de decidir, é crítica.

**Notebook como servidor (opção 1).**

- A vantagem é funcionar sem internet.
- A desvantagem é concentrar no notebook o terminal, o servidor, o banco e o backup: um único ponto de falha num ambiente de oficina, com poeira, quedas, risco de roubo e desligamento no fim do dia.
- Na prática a manutenção remota também é pior. Ela depende de a máquina estar ligada e online, e é provável que seja Windows doméstico.
- Usar o notebook como servidor exigiria quatro coisas:
  - Linux, ou WSL2 com serviço que sobe no boot;
  - criptografia de disco (BitLocker/LUKS);
  - backup off-site automático;
  - nobreak.

**Latência.**

- Quem tem região em SP: Lightsail, EC2/RDS, Magalu, Oracle e Fly gru.
- Os PaaS baratos (Render e Railway) e as VPS europeias rodam nos EUA ou na Europa, com 120–250 ms de RTT. Para um app com várias chamadas tRPC por tela, isso é perceptível, mas tolerável.
- Hospedar no Brasil também simplifica a conversa de LGPD sobre transferência internacional (art. 33). Esse ponto fica para o agente `seguranca`.

**Domínio, DNS e HTTPS.**

- Sugestão: um .com.br da oficina, com um subdomínio como `os.<dominio>`.
- Na VPS ou no Lightsail, o Caddy emite e renova o certificado Let's Encrypt sozinho.
- O DNS pode ficar no Route 53 (US$ 0,50) para tudo ficar no Terraform, ou no registro.br/Cloudflare de graça.
- Nos PaaS o HTTPS é automático.

**Acesso remoto para manutenção.**

- **Na nuvem:** SSH por chave com a porta 22 restrita, browser SSH do console da AWS, ou Tailscale na instância para não expor nada além de 80/443.
- **No notebook da recepção** (suporte à usuária, não servidor): RustDesk ou AnyDesk, mais Tailscale se precisar de shell.

**Esforço de provisionamento** (IaC simples, sem Kubernetes):

- **Lightsail:** um módulo Terraform com instância, IP estático, portas 80/443 e snapshot automático diário, mais o registro DNS. O cloud-init instala Docker + Compose e sobe `app + db + caddy`. Estimativa: ≈ 2–4 h até o "hello world" com HTTPS.
- **EC2 + RDS:** 1–2 dias, por causa de VPC, SGs, subnet group, SSM e parameter group. Não se justifica nessa escala.

**Lock-in.**

- Na opção recomendada é baixo: é VM + Docker Compose + banco padrão, e migrar para Magalu ou outra VPS é um `pg_dump`/`mysqldump` mais um `terraform apply` em outro provider.
- Nos PaaS é médio: build, config, banco gerenciado e região.

**Observação sobre o app atual.**

- O app depende de **Manus OAuth** (`OAUTH_SERVER_URL`, `VITE_APP_ID`, `OWNER_OPEN_ID`) e de **Manus Forge** (`BUILT_IN_FORGE_API_*`, storage).
- Fora da plataforma Manus, essas dependências precisam ser substituídas, em qualquer opção de hospedagem.
- O banco é MySQL (Drizzle, `dialect: "mysql"`). Isso elimina o Render se o app for mantido, porque o Render só tem Postgres gerenciado.
- A decisão sobre o app é do `arquiteto`. A recomendação de infra vale para qualquer das três rotas: reaproveitar, adotar open source ou reescrever.

**Híbrido (nuvem + cache/offline).**

- Faria sentido com várias usuárias e internet ruim comprovada.
- Para 1 usuária, o custo é alto: Service Worker + IndexedDB + fila de sincronização + conflitos, sem contar que a numeração de OS gerada offline exige um esquema próprio.
- Recomendo reavaliar só se a P1 mostrar quedas frequentes durante o expediente. Antes disso, prefiro um link 4G dedicado com failover (seção 5), que resolve o mesmo problema sem código.

## 5. Lado físico da oficina

**Notebook da recepção.**

- Atalho na área de trabalho e na barra de tarefas abrindo o Chrome/Edge em modo app (`--app=https://os.<dominio>`), ou o app instalado como PWA. Uma janela só, sem abas nem barra de endereço.
- Login do Windows automático ou simples, e sessão do sistema persistente com cookie de longa duração.
- Atualizações do Windows fora do horário comercial.
- Criptografia de disco ligada. Mesmo com os dados na nuvem, o navegador guarda sessão e PDFs baixados.

**Impressão da OS.**

- Impressora **laser monocromática A4 USB** (ou Wi-Fi), imprimindo direto do navegador com CSS `@media print` e layout de OS de 1 página.
- Evitar jato de tinta, que resseca com o uso esporádico de oficina, e evitar térmica, porque a OS tem tabela de itens e campo de assinatura.
- Modelo e preço ficam a cotar. Laser mono de entrada costuma ser o menor custo por página.
- Alternativa sem impressora: PDF por WhatsApp. Essa definição depende do dono (item "Saída da OS" de `docs/negocio.md`).

**Plano B para queda de internet.**

1. **Imediato e sem custo:** roteamento (hotspot) do celular da recepcionista ou do dono. O consumo do sistema é desprezível, dezenas de MB por dia.
2. **Se a P1 mostrar instabilidade:** um modem/roteador 4G com chip dedicado (pré-pago ou controle barato), ligado como failover no roteador da oficina ou deixado à mão para conectar ao notebook. O custo de aparelho e chip fica a cotar.
3. **Contingência total:** bloco de OS em papel com numeração reservada (ex.: série "C-001…"), lançado no sistema quando a conexão voltar. Isso é processo, não infra, mas precisa existir desde o dia 1.

## 6. Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Internet da oficina instável ou ruim | Sistema indisponível na recepção | Medir antes (P1). Hotspot 4G, roteador 4G de failover, bloco de papel de contingência. |
| Banco no mesmo host do app (sem RDS) | Perda de dados se a instância corromper | Snapshot diário do Lightsail + dump lógico diário em S3 com restore testado (responsabilidade do `sre`) |
| Pagamento em US$ (câmbio + IOF) | Custo flutua ±15% | Valor absoluto baixo. Faturamento em R$ pela AWS Brasil, ou Magalu se fizer questão de R$. |
| Wesley é o único que opera | Fator ônibus = 1 | IaC versionado + README de operação. Infra simples o bastante para um terceiro assumir. |
| Oracle Free: instância recuperada por ociosidade ou conta suspensa | Indisponibilidade sem aviso | Não usar em produção. No máximo como ambiente de testes. |
| Promoções (Hostinger, Contabo) exigem 24 meses e renovam mais caro | Custo maior depois | Considerar o preço de renovação na decisão |
| Dados de clientes em servidor fora do Brasil (PaaS dos EUA) | Exige base legal de transferência internacional na LGPD | Preferir região SP. Validar com `seguranca`. |
| Notebook roubado | Vazamento de sessão/PDFs | Criptografia de disco, sessão revogável no servidor, senha no Windows |

## 7. Premissas e pendências

- **P1 (crítica):** medir a internet da oficina por 1–2 semanas antes do go-live.
  - Como: um script no notebook registrando ping para 1.1.1.1 e para o endpoint do Lightsail SP, mais `curl` com tempo de resposta a cada minuto, mais um speedtest diário.
  - Quem e o que decide: o `sre`/Wesley analisa o resultado. Se a disponibilidade em horário comercial ficar abaixo de ~99%, reavaliar entre roteador 4G de failover e notebook local.
- **P2:** volume baixo, da ordem de dezenas de OS por dia no máximo, e 1 usuária. Um host de 1–2 GB sobra.
- **P3:** horário comercial. Uma janela de manutenção à noite ou no domingo é aceitável, e não é preciso alta disponibilidade nem Multi-AZ.
- **P4:** Wesley já tem conta AWS. Uma conta nova traria créditos do free tier atual, mas isso não muda a decisão.
- **P5:** preços conferidos em 15/10/2026.
  - Valores marcados "a confirmar" vieram de terceiros: Magalu, Hostinger, Contabo, Render, e Hetzner, que reajustou preços em abr e jun/2026 e mostra planos compartilhados como "indisponíveis".
  - A AWS foi conferida na Price List API oficial de `sa-east-1`.
  - O Fly gru é uma estimativa feita com o markup regional.
- **P6:** a stack ainda não está decidida. A recomendação (VM + Docker Compose) atende Node+MySQL, Node+Postgres, um open source em PHP/Python, ou uma reescrita.
- **Pendências com o dono:**
  - confirmar a internet atual (provedor e plano);
  - dizer se há um celular com dados para o hotspot;
  - dizer se quer a OS impressa ou em PDF por WhatsApp;
  - definir quem registra o domínio (CPF ou CNPJ da oficina).
