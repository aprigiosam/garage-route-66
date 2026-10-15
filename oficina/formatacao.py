from decimal import Decimal


def brl(valor):
    """Decimal('4526.5') -> 'R$ 4.526,50' (sem depender de locale do sistema)."""
    texto = f"{Decimal(valor):,.2f}"  # 4,526.50
    return "R$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")
