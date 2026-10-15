from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from balcao.views import buscar
from oficina.models import Cliente, ItemOS, OrdemServico, Veiculo

S = OrdemServico.Status


# Hash de senha rápido só nos testes (PBKDF2 é lento de propósito e dominava o tempo da suíte).
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = User.objects.create_user("recepcao", password="x")
        cls.cliente = Cliente.objects.create(nome="Henrique", telefone="11943796788")
        cls.veiculo = Veiculo.objects.create(placa="FIB3F99", marca="Kia", modelo="Sportage", cliente=cls.cliente)

    def setUp(self):
        self.client.force_login(self.usuario)

    def nova_os(self, **kwargs):
        return OrdemServico.objects.create(cliente=self.cliente, veiculo=self.veiculo, relato_cliente="Barulho", **kwargs)

    def url(self, nome, os=None, **kw):
        args = [os.numero] + list(kw.values()) if os else None
        return reverse(f"balcao:{nome}", args=args)


class AcessoTests(Base):
    def test_telas_exigem_login(self):
        self.client.logout()
        os = self.nova_os()
        for url in (self.url("quadro"), self.url("os_nova"), self.url("os_detalhe", os)):
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 302)
                self.assertIn(reverse("login"), resp.url)

    def test_login_page_e_assets_vendorizados(self):
        self.client.logout()
        self.assertContains(self.client.get(reverse("login")), "GARAGE ROUTE 66")
        vendor = Path(settings.BASE_DIR, "balcao/static/balcao/vendor")
        for arquivo in ("bootstrap.min.css", "bootstrap.bundle.min.js", "htmx.min.js"):
            self.assertTrue((vendor / arquivo).stat().st_size > 10_000, arquivo)

    def test_acoes_exigem_post(self):
        os = self.nova_os()
        self.assertEqual(self.client.get(self.url("os_status", os)).status_code, 405)


class QuadroTests(Base):
    def test_colunas_mostram_so_os_em_andamento(self):
        aberta = self.nova_os()
        cancelada = self.nova_os()
        cancelada.alterar_status(S.CANCELADA)
        resp = self.client.get(self.url("quadro"))
        numeros = [o.numero for _, ordens in resp.context["colunas"] for o in ordens]
        self.assertEqual(numeros, [aberta.numero])
        self.assertContains(resp, "FIB3F99")

    def test_busca_htmx_devolve_so_o_miolo(self):
        self.nova_os()
        resp = self.client.get(self.url("quadro"), {"q": "fib3f"}, HTTP_HX_REQUEST="true")
        self.assertNotContains(resp, "<html")
        self.assertContains(resp, "FIB3F99")
        self.assertEqual(len(resp.context["resultados"]), 1)

    def test_buscar_por_placa_nome_telefone_e_numero(self):
        os = self.nova_os()
        outro = Cliente.objects.create(nome="Maria", telefone="1155551234")
        OrdemServico.objects.create(cliente=outro, relato_cliente="x",
                                    veiculo=Veiculo.objects.create(placa="ABC1234", cliente=outro))
        qs = OrdemServico.objects.all()
        for termo in ("fib-3f99", "henri", "94379", str(os.numero)):
            with self.subTest(termo=termo):
                self.assertIn(os, buscar(qs, termo))
        self.assertNotIn(os, buscar(qs, "Maria"))
        self.assertEqual(buscar(qs, "  ").count(), 2)


class NovaOSTests(Base):
    def test_placa_nova_cria_cliente_veiculo_e_os(self):
        resp = self.client.post(self.url("os_nova"), {
            "placa": "abc-1d23", "nome": "João", "telefone": "(11) 5555-1234", "marca": "VW", "modelo": "Gol",
            "km_entrada": "120000", "relato_cliente": "Freio fazendo barulho",
        })
        os = OrdemServico.objects.get()
        self.assertRedirects(resp, self.url("os_detalhe", os))
        self.assertEqual((os.veiculo.placa, os.cliente.nome, os.cliente.telefone), ("ABC1D23", "João", "1155551234"))

    def test_placa_existente_reaproveita_veiculo_e_cliente(self):
        self.client.post(self.url("os_nova"), {"placa": "FIB3F99", "relato_cliente": "Revisão"})
        os = OrdemServico.objects.get()
        self.assertEqual((os.veiculo, os.cliente), (self.veiculo, self.cliente))
        self.assertEqual(Cliente.objects.count(), 1)

    def test_documento_existente_reaproveita_cliente_com_carro_novo(self):
        Cliente.objects.filter(pk=self.cliente.pk).update(documento="52998224725")
        self.client.post(self.url("os_nova"), {"placa": "XYZ9876", "nome": "Outro nome",
                                               "documento": "529.982.247-25", "relato_cliente": "x"})
        self.assertEqual(OrdemServico.objects.get().cliente, self.cliente)

    def test_placa_nova_sem_nome_e_rejeitada(self):
        resp = self.client.post(self.url("os_nova"), {"placa": "XYZ9876", "relato_cliente": "x"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Veículo novo: informe o nome do cliente.")
        self.assertFalse(OrdemServico.objects.exists())

    def test_placa_info_htmx(self):
        self.assertContains(self.client.get(self.url("placa_info"), {"placa": "fib3f99"}), "Henrique")
        self.assertContains(self.client.get(self.url("placa_info"), {"placa": "XYZ9876"}), "Placa nova")


class DetalheTests(Base):
    def test_fluxo_completo_pelo_balcao(self):
        os = self.nova_os()
        self.client.post(self.url("item_adicionar", os), {
            "tipo": "peca", "descricao": "Braço suspensão", "quantidade": "2", "valor_unitario": "154,00",
            "origem": "fornecedor"})
        self.client.post(self.url("item_adicionar", os), {
            "tipo": "servico", "descricao": "Suspensão traseira", "quantidade": "1", "valor_unitario": "600,00"})
        resp = self.client.get(self.url("os_detalhe", os))
        self.assertEqual(resp.context["total_geral"], Decimal("908.00"))
        self.assertContains(resp, "R$ 908,00")

        self.client.post(self.url("os_decisao", os), {"decisao": "aprovado", "canal": "whatsapp", "nome": "Henrique"})
        self.client.post(self.url("os_status", os), {"destino": "em_execucao"})
        self.client.post(self.url("os_status", os), {"destino": "pronta"})
        self.client.post(self.url("os_entregar", os), {"forma_pagamento": "pix"})
        os.refresh_from_db()
        self.assertEqual((os.status, os.forma_pagamento), (S.ENTREGUE, "pix"))
        self.assertEqual(os.aprovacoes.get().valor, Decimal("908.00"))

    def test_item_invalido_mostra_erro(self):
        os = self.nova_os()
        resp = self.client.post(self.url("item_adicionar", os), {
            "tipo": "peca", "descricao": "Batente", "quantidade": "1", "valor_unitario": "10"})
        self.assertEqual(resp.status_code, 400)
        self.assertContains(resp, "Informe a origem da peça.", status_code=400)

    def test_decisao_sem_itens_mostra_erro(self):
        os = self.nova_os()
        resp = self.client.post(self.url("os_decisao", os), {"decisao": "aprovado", "canal": "presencial", "nome": "H"})
        self.assertContains(resp, "O orçamento não tem itens.", status_code=400)

    def test_atalho_nao_pula_formularios_obrigatorios(self):
        os = self.nova_os()
        self.client.post(self.url("os_status", os), {"destino": "aprovada"})
        os.refresh_from_db()
        self.assertEqual(os.status, S.ORCAMENTO)

    def test_devolver_peca(self):
        os = self.nova_os()
        item = ItemOS.objects.create(os=os, tipo="peca", descricao="Disco", valor_unitario=Decimal("600"),
                                     origem="fornecedor")
        self.client.post(self.url("item_situacao", os, item_id=item.pk), {"situacao": "devolvido", "motivo": "Tamanho errado"})
        item.refresh_from_db()
        self.assertEqual((item.situacao, item.motivo_situacao), ("devolvido", "Tamanho errado"))
        self.assertEqual(os.total(), Decimal("0.00"))

    def test_proximo_passo_mostra_so_acoes_validas(self):
        os = self.nova_os()
        resp = self.client.get(self.url("os_detalhe", os))
        self.assertIsNotNone(resp.context["decisao_form"])
        self.assertIsNone(resp.context["entrega_form"])
        self.assertEqual(resp.context["acoes"], [S.CANCELADA])
