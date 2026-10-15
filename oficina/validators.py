"""Validação e normalização de dados brasileiros: CPF, CNPJ, placa e telefone.

Portado e simplificado de `legado/validators.py` (commit e771b139).

Convenção:
- `normalizar_*` devolve o valor canônico que é gravado no banco (sem máscara).
- `validar_*` levanta `ValidationError`; o Django usa isso nos campos dos models e forms.
"""

import re

from django.core.exceptions import ValidationError

PESOS_CPF_1 = range(10, 1, -1)  # 10..2
PESOS_CPF_2 = range(11, 1, -1)  # 11..2
PESOS_CNPJ_1 = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
PESOS_CNPJ_2 = (6, *PESOS_CNPJ_1)

# Placa antiga (ABC1234) e Mercosul (ABC1D23) diferem só no 5º caractere.
PADRAO_PLACA = re.compile(r"[A-Z]{3}[0-9][A-Z0-9][0-9]{2}")
# CNPJ alfanumérico (Receita, a partir de jul/2026): 12 caracteres A-Z/0-9 + 2 DVs numéricos.
PADRAO_CNPJ = re.compile(r"[A-Z0-9]{12}[0-9]{2}")


def _digito_verificador(base, pesos):
    """Módulo 11 usado por CPF e CNPJ. `ord(c) - 48` vale para dígitos e letras (CNPJ alfanumérico)."""
    resto = sum((ord(c) - 48) * p for c, p in zip(base, pesos)) % 11
    return "0" if resto < 2 else str(11 - resto)


def somente_digitos(valor):
    return re.sub(r"\D", "", valor or "")


def normalizar_cpf(valor):
    return somente_digitos(valor)


def validar_cpf(valor):
    cpf = normalizar_cpf(valor)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido.", code="cpf_invalido")
    d1 = _digito_verificador(cpf[:9], PESOS_CPF_1)
    d2 = _digito_verificador(cpf[:9] + d1, PESOS_CPF_2)
    if cpf[9:] != d1 + d2:
        raise ValidationError("CPF inválido.", code="cpf_invalido")


def normalizar_cnpj(valor):
    return re.sub(r"[^A-Z0-9]", "", (valor or "").upper())


def validar_cnpj(valor):
    cnpj = normalizar_cnpj(valor)
    if not PADRAO_CNPJ.fullmatch(cnpj) or cnpj == cnpj[0] * 14:
        raise ValidationError("CNPJ inválido.", code="cnpj_invalido")
    d1 = _digito_verificador(cnpj[:12], PESOS_CNPJ_1)
    d2 = _digito_verificador(cnpj[:12] + d1, PESOS_CNPJ_2)
    if cnpj[12:] != d1 + d2:
        raise ValidationError("CNPJ inválido.", code="cnpj_invalido")


def normalizar_placa(valor):
    return re.sub(r"[^A-Z0-9]", "", (valor or "").upper())


def validar_placa(valor):
    if not PADRAO_PLACA.fullmatch(normalizar_placa(valor)):
        raise ValidationError(
            "Placa inválida. Use o formato ABC1234 ou ABC1D23.", code="placa_invalida"
        )


def normalizar_documento(valor):
    return normalizar_cnpj(valor)  # CPF normalizado é subconjunto (só dígitos)


def validar_documento(valor):
    """CPF (11 dígitos) ou CNPJ (14 caracteres, numérico ou alfanumérico)."""
    if len(normalizar_documento(valor)) == 11:
        validar_cpf(valor)
    else:
        validar_cnpj(valor)


# Fixo: DDD + 8 dígitos. Celular: DDD + 9 + 8 dígitos. DDD não começa com 0.
PADRAO_TELEFONE = re.compile(r"[1-9][0-9](9?[0-9]{8})")


def normalizar_telefone(valor):
    return somente_digitos(valor)


def validar_telefone(valor):
    tel = normalizar_telefone(valor)
    if not PADRAO_TELEFONE.fullmatch(tel) or (len(tel) == 11 and tel[2] != "9"):
        raise ValidationError("Telefone inválido. Informe DDD + número.", code="telefone_invalido")
