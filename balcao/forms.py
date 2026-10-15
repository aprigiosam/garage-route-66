from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from oficina import validators as v
from oficina.models import Aprovacao, Cliente, ItemOS, OrdemServico, Veiculo


class BootstrapMixin:
    """Aplica as classes do Bootstrap nos widgets (evita depender de biblioteca de templates)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            classe = "form-select" if isinstance(campo.widget, forms.Select) else "form-control"
            campo.widget.attrs.setdefault("class", classe)


class NovaOSForm(BootstrapMixin, forms.Form):
    """Abre uma OS a partir da placa. Placa nova cria cliente e veículo no mesmo passo."""

    placa = forms.CharField(max_length=8, validators=[v.validar_placa])
    nome = forms.CharField(label="Nome do cliente", max_length=120, required=False)
    telefone = forms.CharField(max_length=20, required=False, validators=[v.validar_telefone])
    documento = forms.CharField(label="CPF/CNPJ", max_length=20, required=False, validators=[v.validar_documento])
    marca = forms.CharField(max_length=40, required=False)
    modelo = forms.CharField(max_length=60, required=False)
    ano = forms.IntegerField(min_value=1950, max_value=2100, required=False,
                             widget=forms.TextInput(attrs={"inputmode": "numeric"}))
    km_entrada = forms.IntegerField(label="Km de entrada", min_value=0, required=False,
                                    widget=forms.TextInput(attrs={"inputmode": "numeric"}))
    relato_cliente = forms.CharField(label="O que o cliente relatou", widget=forms.Textarea(attrs={"rows": 3}))

    def clean_placa(self):
        return v.normalizar_placa(self.cleaned_data["placa"])

    def clean(self):
        dados = super().clean()
        placa = dados.get("placa")
        self.veiculo = Veiculo.objects.select_related("cliente").filter(placa=placa).first() if placa else None
        if placa and not self.veiculo and not dados.get("nome"):
            self.add_error("nome", "Veículo novo: informe o nome do cliente.")
        return dados

    def save(self):
        d = self.cleaned_data
        with transaction.atomic():
            veiculo = self.veiculo
            if veiculo is None:
                documento = v.normalizar_documento(d["documento"])
                # Cliente que já existe (mesmo documento) trazendo outro carro: reaproveita o cadastro.
                cliente = Cliente.objects.filter(documento=documento).first() if documento else None
                if cliente is None:
                    cliente = Cliente(nome=d["nome"], telefone=d["telefone"], documento=d["documento"])
                    cliente.full_clean()
                    cliente.save()
                veiculo = Veiculo(placa=d["placa"], marca=d["marca"], modelo=d["modelo"], ano=d["ano"],
                                  cliente=cliente)
                veiculo.full_clean()
                veiculo.save()
            os = OrdemServico(cliente=veiculo.cliente, veiculo=veiculo, km_entrada=d["km_entrada"],
                              relato_cliente=d["relato_cliente"])
            os.full_clean(exclude=["numero"])
            os.save()
        return os


DECIMAL = {"inputmode": "decimal", "autocomplete": "off"}


class ItemForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = ItemOS
        fields = ["tipo", "descricao", "quantidade", "valor_unitario", "origem", "fornecedor"]
        # Texto com teclado numérico: aceita "154,00" (o input type=number dos navegadores varia com o idioma).
        widgets = {"quantidade": forms.TextInput(attrs=DECIMAL), "valor_unitario": forms.TextInput(attrs=DECIMAL)}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ("quantidade", "valor_unitario"):
            self.fields[campo].localize = True
        self.fields["tipo"].choices = ItemOS.Tipo.choices  # sem a opção vazia
        self.fields["tipo"].initial = ItemOS.Tipo.PECA
        self.fields["origem"].choices = [("", "— (serviço)")] + ItemOS.Origem.choices
        self.fields["fornecedor"].empty_label = "— (opcional)"
        self.fields["valor_unitario"].initial = None


class DecisaoForm(BootstrapMixin, forms.Form):
    decisao = forms.ChoiceField(label="Resposta do cliente", choices=Aprovacao.Decisao.choices)
    canal = forms.ChoiceField(choices=Aprovacao.Canal.choices)
    nome = forms.CharField(label="Quem respondeu", max_length=120)

    def save(self, os):
        os.registrar_decisao(self.cleaned_data["decisao"], self.cleaned_data["canal"], self.cleaned_data["nome"])


class EntregaForm(BootstrapMixin, forms.Form):
    forma_pagamento = forms.ChoiceField(label="Forma de pagamento", choices=OrdemServico.FormaPagamento.choices)

    def save(self, os):
        os.forma_pagamento = self.cleaned_data["forma_pagamento"]
        os.alterar_status(OrdemServico.Status.ENTREGUE)


def erros_de(validation_error):
    """Mensagens legíveis de um ValidationError (com ou sem dicionário de campos)."""
    if isinstance(validation_error, ValidationError):
        return " ".join(validation_error.messages)
    return str(validation_error)
