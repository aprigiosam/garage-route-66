"""Domínio da oficina: cliente, veículo, ordem de serviço (OS), itens e aprovação.

Base: docs/pareceres/dba.md, com estas simplificações (ver ADR 0001):
- regras de negócio no Django (testadas) + CHECK/UNIQUE no banco; sem triggers;
- dinheiro em Decimal(10,2) e totais somados em Python (evita float do SQLite em SUM);
- nada é apagado: FKs com PROTECT e exclusão bloqueada no admin.
"""

from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F, Q
from django.utils import timezone

from . import validators as v

DUAS_CASAS = Decimal("0.01")


class Cliente(models.Model):
    nome = models.CharField(max_length=120)
    documento = models.CharField(
        "CPF/CNPJ", max_length=20, blank=True, validators=[v.validar_documento]
    )
    # max_length com folga para a digitação com máscara; no banco o valor fica sempre normalizado.
    telefone = models.CharField(max_length=20, blank=True, validators=[v.validar_telefone])
    observacao = models.TextField("observação", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]
        constraints = [
            # Documento é opcional, mas não pode repetir quando informado.
            models.UniqueConstraint(
                fields=["documento"], condition=~Q(documento=""), name="cliente_documento_unico"
            ),
        ]

    def __str__(self):
        return self.nome

    def normalizar(self):
        self.documento = v.normalizar_documento(self.documento)
        self.telefone = v.normalizar_telefone(self.telefone)

    def clean_fields(self, exclude=None):
        self.normalizar()  # antes das validações de campo (tamanho, formato)
        super().clean_fields(exclude=exclude)

    def save(self, *args, **kwargs):
        self.normalizar()
        super().save(*args, **kwargs)


class Veiculo(models.Model):
    placa = models.CharField(max_length=8, unique=True, validators=[v.validar_placa])  # folga p/ "ABC-1234"
    marca = models.CharField(max_length=40, blank=True)
    modelo = models.CharField(max_length=60, blank=True)
    ano = models.PositiveSmallIntegerField(null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="veiculos")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "veículo"
        ordering = ["placa"]
        constraints = [
            models.CheckConstraint(
                condition=Q(ano__isnull=True) | Q(ano__gte=1950, ano__lte=2100), name="veiculo_ano_valido"
            ),
        ]

    def __str__(self):
        return " ".join(filter(None, [self.placa, self.marca, self.modelo]))

    def clean_fields(self, exclude=None):
        self.placa = v.normalizar_placa(self.placa)
        super().clean_fields(exclude=exclude)

    def save(self, *args, **kwargs):
        self.placa = v.normalizar_placa(self.placa)
        super().save(*args, **kwargs)


class Fornecedor(models.Model):
    nome = models.CharField(max_length=80, unique=True)
    telefone = models.CharField(max_length=20, blank=True, validators=[v.validar_telefone])

    def clean_fields(self, exclude=None):
        self.telefone = v.normalizar_telefone(self.telefone)
        super().clean_fields(exclude=exclude)

    def save(self, *args, **kwargs):
        self.telefone = v.normalizar_telefone(self.telefone)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["nome"]
        verbose_name_plural = "fornecedores"

    def __str__(self):
        return self.nome


class Contador(models.Model):
    """Numeração sequencial sem buracos (AUTOINCREMENT pula números em rollback)."""

    nome = models.CharField(max_length=20, primary_key=True)
    ultimo_valor = models.PositiveIntegerField(default=0)

    @classmethod
    def proximo(cls, nome):
        # Chamar dentro de transaction.atomic(): o UPDATE trava a escrita até o commit.
        cls.objects.get_or_create(nome=nome)
        cls.objects.filter(nome=nome).update(ultimo_valor=F("ultimo_valor") + 1)
        return cls.objects.get(nome=nome).ultimo_valor


class StatusOS(models.TextChoices):
    ORCAMENTO = "orcamento", "Orçamento"
    APROVADA = "aprovada", "Aprovada"
    EM_EXECUCAO = "em_execucao", "Em execução"
    PRONTA = "pronta", "Pronta"
    ENTREGUE = "entregue", "Entregue"
    RECUSADA = "recusada", "Recusada"
    CANCELADA = "cancelada", "Cancelada"


class OrdemServico(models.Model):
    Status = StatusOS

    class FormaPagamento(models.TextChoices):
        DINHEIRO = "dinheiro", "Dinheiro"
        PIX = "pix", "PIX"
        DEBITO = "debito", "Cartão de débito"
        CREDITO = "credito", "Cartão de crédito"

    S = Status
    TRANSICOES = {
        S.ORCAMENTO: {S.APROVADA, S.RECUSADA, S.CANCELADA},
        S.APROVADA: {S.EM_EXECUCAO, S.CANCELADA},
        S.EM_EXECUCAO: {S.PRONTA},
        S.PRONTA: {S.ENTREGUE},
        S.RECUSADA: {S.ORCAMENTO},  # cliente reconsiderou
        S.ENTREGUE: set(),
        S.CANCELADA: set(),
    }
    # Itens podem ser ajustados até a OS ficar pronta (orçamento complementar no meio do serviço).
    STATUS_EDITAVEIS = {S.ORCAMENTO, S.APROVADA, S.EM_EXECUCAO}

    numero = models.PositiveIntegerField("nº", unique=True, editable=False)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="ordens")
    veiculo = models.ForeignKey(Veiculo, on_delete=models.PROTECT, related_name="ordens")
    km_entrada = models.PositiveIntegerField("km de entrada", null=True, blank=True)
    relato_cliente = models.TextField("relato do cliente")
    diagnostico = models.TextField("diagnóstico", blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ORCAMENTO, editable=False)
    forma_pagamento = models.CharField(
        "forma de pagamento", max_length=10, choices=FormaPagamento.choices, blank=True
    )
    aberta_em = models.DateTimeField(default=timezone.now)
    entregue_em = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "ordem de serviço"
        verbose_name_plural = "ordens de serviço"
        ordering = ["-numero"]
        indexes = [models.Index(fields=["veiculo", "aberta_em"]), models.Index(fields=["status"])]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=StatusOS.values), name="os_status_valido"
            ),
        ]

    def __str__(self):
        return f"OS {self.numero}"

    def clean(self):
        if self.veiculo_id and self.cliente_id and self.veiculo.cliente_id != self.cliente_id:
            raise ValidationError({"veiculo": "Este veículo pertence a outro cliente."})

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.numero is None:
                self.numero = Contador.proximo("os")
            super().save(*args, **kwargs)

    # --- Regras de negócio ---------------------------------------------------

    def itens_ativos(self):
        return [i for i in self.itens.all() if i.situacao == ItemOS.Situacao.ATIVO]

    def total(self, tipo=None):
        itens = [i for i in self.itens_ativos() if tipo is None or i.tipo == tipo]
        return sum((i.valor_total for i in itens), Decimal("0.00"))

    @property
    def editavel(self):
        return self.status in self.STATUS_EDITAVEIS

    def alterar_status(self, novo, motivo=""):
        novo = self.Status(novo)
        if novo not in self.TRANSICOES[self.Status(self.status)]:
            raise ValidationError(
                f"Não é possível passar de {self.get_status_display()} para {novo.label}."
            )
        if novo == self.Status.ENTREGUE:
            if not self.forma_pagamento:
                raise ValidationError("Informe a forma de pagamento antes de entregar.")
            self.entregue_em = timezone.now()
        with transaction.atomic():
            HistoricoStatus.objects.create(os=self, de=self.status, para=novo, motivo=motivo)
            self.status = novo
            self.save()

    def registrar_decisao(self, decisao, canal, nome):
        """Registra a resposta do cliente ao orçamento e move a OS para aprovada/recusada."""
        if not self.itens_ativos():
            raise ValidationError("O orçamento não tem itens.")
        with transaction.atomic():
            aprovacao = Aprovacao.objects.create(
                os=self, decisao=decisao, canal=canal, nome=nome, valor=self.total()
            )
            destino = self.Status.APROVADA if decisao == Aprovacao.Decisao.APROVADO else self.Status.RECUSADA
            self.alterar_status(destino)
        return aprovacao


class ItemOS(models.Model):
    class Tipo(models.TextChoices):
        PECA = "peca", "Peça"
        SERVICO = "servico", "Serviço"

    class Origem(models.TextChoices):
        FORNECEDOR = "fornecedor", "Fornecedor"
        CLIENTE = "cliente", "Trazida pelo cliente"

    class Situacao(models.TextChoices):
        ATIVO = "ativo", "Ativo"
        DEVOLVIDO = "devolvido", "Devolvido ao fornecedor"
        REMOVIDO = "removido", "Removido"

    os = models.ForeignKey(OrdemServico, on_delete=models.PROTECT, related_name="itens")
    tipo = models.CharField(max_length=8, choices=Tipo.choices)
    descricao = models.CharField("descrição", max_length=200)
    quantidade = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal("1"))
    valor_unitario = models.DecimalField("valor unitário", max_digits=10, decimal_places=2, default=Decimal("0"))
    origem = models.CharField(max_length=10, choices=Origem.choices, blank=True)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT, null=True, blank=True)
    situacao = models.CharField("situação", max_length=10, choices=Situacao.choices, default=Situacao.ATIVO)
    motivo_situacao = models.CharField("motivo", max_length=200, blank=True)

    class Meta:
        verbose_name = "item"
        constraints = [
            models.CheckConstraint(condition=Q(quantidade__gt=0), name="item_quantidade_positiva"),
            models.CheckConstraint(condition=Q(valor_unitario__gte=0), name="item_valor_nao_negativo"),
            # Serviço não tem origem nem fornecedor; peça sempre tem origem.
            models.CheckConstraint(
                condition=Q(tipo="peca", origem__in=["fornecedor", "cliente"])
                | Q(tipo="servico", origem="", fornecedor__isnull=True),
                name="item_origem_coerente",
            ),
            models.CheckConstraint(
                condition=Q(origem="fornecedor") | Q(fornecedor__isnull=True),
                name="item_fornecedor_so_com_origem_fornecedor",
            ),
            # Peça trazida pelo cliente não é cobrada.
            models.CheckConstraint(
                condition=~Q(origem="cliente") | Q(valor_unitario=0), name="item_peca_cliente_sem_valor"
            ),
        ]

    def __str__(self):
        return self.descricao

    @property
    def valor_total(self):
        # Arredondamento comercial (meio para cima); o padrão do Decimal é o bancário (meio para o par).
        return (self.quantidade * self.valor_unitario).quantize(DUAS_CASAS, rounding=ROUND_HALF_UP)

    def clean(self):
        if self.os_id and not self.os.editavel and not self._apenas_situacao_mudou():
            raise ValidationError("A OS não aceita mais alterações de itens neste status.")
        if self.tipo == self.Tipo.SERVICO:
            self.origem, self.fornecedor = "", None
        elif not self.origem:
            raise ValidationError({"origem": "Informe a origem da peça."})
        if self.origem == self.Origem.CLIENTE:
            self.valor_unitario = Decimal("0")
        if self.origem != self.Origem.FORNECEDOR:
            self.fornecedor = None

    def _apenas_situacao_mudou(self):
        # Devolução de peça ao fornecedor é permitida mesmo com a OS pronta.
        if not self.pk:
            return False
        antigo = ItemOS.objects.get(pk=self.pk)
        campos = ["tipo", "descricao", "quantidade", "valor_unitario", "origem", "fornecedor_id"]
        return all(getattr(antigo, c) == getattr(self, c) for c in campos)


class Aprovacao(models.Model):
    class Decisao(models.TextChoices):
        APROVADO = "aprovado", "Aprovado"
        RECUSADO = "recusado", "Recusado"

    class Canal(models.TextChoices):
        PRESENCIAL = "presencial", "Presencial"
        TELEFONE = "telefone", "Telefone"
        WHATSAPP = "whatsapp", "WhatsApp"

    os = models.ForeignKey(OrdemServico, on_delete=models.PROTECT, related_name="aprovacoes")
    decisao = models.CharField("decisão", max_length=8, choices=Decisao.choices)
    canal = models.CharField(max_length=10, choices=Canal.choices)
    nome = models.CharField("quem decidiu", max_length=120)
    valor = models.DecimalField("valor do orçamento", max_digits=10, decimal_places=2)  # foto no momento
    em = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "aprovação"
        verbose_name_plural = "aprovações"
        ordering = ["-em"]


class HistoricoStatus(models.Model):
    os = models.ForeignKey(OrdemServico, on_delete=models.PROTECT, related_name="historico")
    de = models.CharField(max_length=12)
    para = models.CharField(max_length=12)
    motivo = models.CharField(max_length=200, blank=True)
    em = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "histórico de status"
        verbose_name_plural = "histórico de status"
        ordering = ["em"]
