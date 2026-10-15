# Garage Route 66 — Contexto do negócio

Oficina de mecânica em geral (multimarcas). Rua Bem Te Vi, 32 — Vargem Grande, Parelheiros, São Paulo/SP.
WhatsApp: (11) 94379-6788. Aceita cartões.

## Objetivo

Tirar a ordem de serviço (OS) do papel e **entrar em produção o quanto antes**.

## Quem usa

- **Recepcionista**: é quem lança tudo no sistema. É a única usuária no início.
- **Mecânico**: faz o diagnóstico e o orçamento. Hoje não usa o sistema; repassa as informações à recepção.
- **Equipamento**: **um único notebook** na oficina. Não há servidor, outros PCs nem tablets.

## Fluxo atual

1. O cliente chega e relata um problema específico.
2. O mecânico diagnostica.
3. O mecânico monta o orçamento (peças e serviços).
4. O cliente aprova ou recusa.
5. O serviço é executado. Peças vêm de fornecedores (ex.: "Primo", autopeças) ou do próprio cliente.
6. A OS é fechada com o valor total.

Status implícitos: `orçamento → aprovada → em execução → pronta → entregue` (+ `recusada`).

## A OS em papel hoje (exemplo real de 03/09/2026)

Formulário de gráfica com: Data, Nome, CPF/CNPJ, Telefone, tabela (Quant., Discriminação, Unitário, Total) e Valor Total.

Problemas observados:
- **Sem campos de veículo**: modelo e placa vão escritos dentro do campo "Nome".
- **CPF e telefone** ficam em branco na prática.
- **Peças e serviços misturados** na mesma lista; a linha "mão de obra" fica sem valor.
- Preço unitário quase nunca é preenchido; **o total é somado à mão**.
- **Sem número de OS**, status, aprovação/assinatura do cliente, pagamento ou garantia.
- **O verso é usado para controlar peças**, porque o formulário não comporta:
  - peças **devolvidas ao fornecedor** (ex.: disco do tamanho errado);
  - peças **trazidas pelo cliente** (ex.: kit de amortecedor);
  - peças compradas em **autopeças**.

## Requisitos candidatos da V1

1. Cadastro de **cliente + veículo** (placa, modelo, km), com histórico por placa.
2. **OS numerada com status** seguindo o fluxo acima.
3. **Itens separados em peça e serviço**; totais calculados pelo sistema.
4. **Origem da peça**: fornecedor, cliente ou devolvida.
5. Registro da **aprovação do orçamento** pelo cliente.

## Em aberto (perguntar ao dono)

- Há margem sobre a peça? (Respondido: **sem estoque**, as peças são cotadas em autopeças a cada OS.)
- Pagamento: formas e parcelamento? (Respondido: **não vende fiado**, o pagamento é registrado na entrega.)
- Saída da OS: impressa, PDF por WhatsApp ou link?
- A aprovação do orçamento hoje é presencial, por telefone ou por WhatsApp?
- Internet na oficina: é estável? (define se a solução pode ser 100% online)
- Backup: quem cuida? O notebook é um ponto único de falha.

## Ativos existentes

- Repo `aprigiosam/GarageRoute66`: app gerado com o Manus. Começou em Django (set/2025) e foi refeito
  em React 19 + Express + tRPC + MySQL/Drizzle (nov/2025). Usa "Manus OAuth". Versiona `node_modules/`
  e `dist/`. **A reutilização está em avaliação.**
- Scan da OS em papel: `~/Downloads/Documento Escaneado.pdf` (fora do repo: tem dados de cliente).
