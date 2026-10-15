from decimal import Decimal


def brl(valor):
    """Decimal('4526.5') -> 'R$ 4.526,50' (sem depender de locale do sistema)."""
    texto = f"{Decimal(valor):,.2f}"  # 4,526.50
    return "R$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")


def telefone(valor):
    """'11943796788' -> '(11) 94379-6788'; '1155551234' -> '(11) 5555-1234'; outro formato: inalterado."""
    if not valor or len(valor) not in (10, 11) or not valor.isdigit():
        return valor or ""
    return f"({valor[:2]}) {valor[2:-4]}-{valor[-4:]}"
