from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import models

from .formatacao import brl
from .models import Aprovacao, Cliente, Fornecedor, HistoricoStatus, ItemOS, OrdemServico, Veiculo

admin.site.site_header = "Garage Route 66"
admin.site.site_title = "Garage Route 66"
admin.site.index_title = "Ordens de serviço"

S = OrdemServico.Status


class SemExclusao:
    """Nada é apagado no sistema (histórico da oficina e LGPD por anonimização, não DELETE)."""

    def has_delete_permission(self, request, obj=None):
        return False


class VeiculoInline(SemExclusao, admin.TabularInline):
    model = Veiculo
    extra = 0
    fields = ["placa", "marca", "modelo", "ano"]


@admin.register(Cliente)
class ClienteAdmin(SemExclusao, admin.ModelAdmin):
    list_display = ["nome", "telefone", "documento"]
    search_fields = ["nome", "telefone", "documento", "veiculos__placa"]
    inlines = [VeiculoInline]


@admin.register(Veiculo)
class VeiculoAdmin(SemExclusao, admin.ModelAdmin):
    list_display = ["placa", "marca", "modelo", "ano", "cliente"]
    search_fields = ["placa", "modelo", "cliente__nome"]
    autocomplete_fields = ["cliente"]


@admin.register(Fornecedor)
class FornecedorAdmin(SemExclusao, admin.ModelAdmin):
    list_display = ["nome", "telefone"]
    search_fields = ["nome"]


class ItemInline(SemExclusao, admin.TabularInline):
    model = ItemOS
    extra = 1
    # Aceita "154,00" (formato brasileiro) na digitação de valores e quantidades.
    formfield_overrides = {models.DecimalField: {"localize": True}}
    fields = ["tipo", "descricao", "quantidade", "valor_unitario", "valor_total_fmt",
              "origem", "fornecedor", "situacao", "motivo_situacao"]
    readonly_fields = ["valor_total_fmt"]
    autocomplete_fields = ["fornecedor"]

    @admin.display(description="total")
    def valor_total_fmt(self, obj):
        return brl(obj.valor_total) if obj.pk else "-"


class AprovacaoInline(SemExclusao, admin.TabularInline):
    model = Aprovacao
    extra = 0
    fields = ["em", "decisao", "canal", "nome", "valor"]
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False  # criada pelo campo "Próximo passo"


class HistoricoInline(SemExclusao, admin.TabularInline):
    model = HistoricoStatus
    extra = 0
    fields = ["em", "de", "para", "motivo"]
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class OrdemServicoForm(forms.ModelForm):
    proximo_status = forms.ChoiceField(label="Próximo passo", required=False)
    canal = forms.ChoiceField(label="Canal da resposta", required=False,
                              choices=[("", "---------")] + Aprovacao.Canal.choices)
    respondido_por = forms.CharField(label="Quem respondeu", required=False)

    class Meta:
        model = OrdemServico
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        atual = S(self.instance.status) if self.instance.pk else None
        destinos = sorted(OrdemServico.TRANSICOES[atual], key=list(S).index) if atual else []
        self.fields["proximo_status"].choices = [("", "— manter —")] + [(d.value, d.label) for d in destinos]

    def clean(self):
        dados = super().clean()
        if dados.get("proximo_status") in (S.APROVADA, S.RECUSADA):
            for campo in ("canal", "respondido_por"):
                if not dados.get(campo):
                    self.add_error(campo, "Obrigatório para registrar a resposta do cliente.")
        return dados


@admin.register(OrdemServico)
class OrdemServicoAdmin(SemExclusao, admin.ModelAdmin):
    form = OrdemServicoForm
    list_display = ["numero", "status", "cliente", "veiculo", "total_fmt", "aberta_em"]
    list_filter = ["status"]
    search_fields = ["=numero", "veiculo__placa", "cliente__nome", "cliente__telefone"]
    autocomplete_fields = ["cliente", "veiculo"]
    readonly_fields = ["numero", "status", "total_pecas", "total_servicos", "total_fmt", "entregue_em"]
    inlines = [ItemInline, AprovacaoInline, HistoricoInline]
    fieldsets = [
        (None, {"fields": ["numero", "status", "cliente", "veiculo", "km_entrada", "aberta_em"]}),
        ("Atendimento", {"fields": ["relato_cliente", "diagnostico"]}),
        ("Valores", {"fields": ["total_pecas", "total_servicos", "total_fmt", "forma_pagamento", "entregue_em"]}),
        ("Próximo passo", {"fields": ["proximo_status", "canal", "respondido_por"]}),
    ]

    @admin.display(description="peças")
    def total_pecas(self, obj):
        return brl(obj.total(ItemOS.Tipo.PECA))

    @admin.display(description="serviços")
    def total_servicos(self, obj):
        return brl(obj.total(ItemOS.Tipo.SERVICO))

    @admin.display(description="total")
    def total_fmt(self, obj):
        return brl(obj.total())

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("cliente", "veiculo").prefetch_related("itens")

    def save_related(self, request, form, formsets, change):
        # Status muda só depois que os itens foram salvos (a aprovação congela o total).
        super().save_related(request, form, formsets, change)
        destino = form.cleaned_data.get("proximo_status")
        if not destino:
            return
        os = form.instance
        try:
            if destino in (S.APROVADA, S.RECUSADA):
                decisao = Aprovacao.Decisao.APROVADO if destino == S.APROVADA else Aprovacao.Decisao.RECUSADO
                os.registrar_decisao(decisao, form.cleaned_data["canal"], form.cleaned_data["respondido_por"])
            else:
                os.alterar_status(destino)
        except ValidationError as erro:
            messages.error(request, " ".join(erro.messages))
