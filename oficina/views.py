from django.db import connection
from django.http import JsonResponse


def saude(request):
    """Healthcheck: 200 se o app responde e o banco está acessível; 503 caso contrário."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:  # qualquer falha de banco = não saudável
        return JsonResponse({"status": "erro", "banco": "indisponivel"}, status=503)
    return JsonResponse({"status": "ok"})
