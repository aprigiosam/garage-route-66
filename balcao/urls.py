from django.urls import path

from . import views

app_name = "balcao"

urlpatterns = [
    path("", views.quadro, name="quadro"),
    path("os/nova/", views.os_nova, name="os_nova"),
    path("os/placa/", views.placa_info, name="placa_info"),
    path("os/<int:numero>/", views.os_detalhe, name="os_detalhe"),
    path("os/<int:numero>/itens/", views.item_adicionar, name="item_adicionar"),
    path("os/<int:numero>/itens/<int:item_id>/situacao/", views.item_situacao, name="item_situacao"),
    path("os/<int:numero>/status/", views.os_status, name="os_status"),
    path("os/<int:numero>/decisao/", views.os_decisao, name="os_decisao"),
    path("os/<int:numero>/entregar/", views.os_entregar, name="os_entregar"),
]
