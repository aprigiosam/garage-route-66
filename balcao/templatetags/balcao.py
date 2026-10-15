from django import template

from oficina.formatacao import brl as _brl
from oficina.formatacao import telefone as _telefone

register = template.Library()

# Cor (classe Bootstrap) de cada status: usada em badges e colunas do quadro.
CORES_STATUS = {
    "orcamento": "warning",
    "aprovada": "info",
    "em_execucao": "primary",
    "pronta": "success",
    "entregue": "secondary",
    "recusada": "danger",
    "cancelada": "dark",
}


@register.filter
def brl(valor):
    return _brl(valor)


@register.filter
def telefone(valor):
    return _telefone(valor)


@register.filter
def cor_status(status):
    return CORES_STATUS.get(str(status), "secondary")
