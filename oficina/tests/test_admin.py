from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from oficina.formatacao import brl, telefone
from oficina.models import Cliente, ItemOS, OrdemServico, Veiculo

S = OrdemServico.Status


class FormatacaoTests(TestCase):
    def test_brl(self):
        self.assertEqual(brl(Decimal("4526")), "R$ 4.526,00")
        self.assertEqual(brl(Decimal("0.5")), "R$ 0,50")
        self.assertEqual(brl(Decimal("1234567.891")), "R$ 1.234.567,89")

    def test_telefone(self):
        self.assertEqual(telefone("11943796788"), "(11) 94379-6788")
        self.assertEqual(telefone("1155551234"), "(11) 5555-1234")
        self.assertEqual(telefone(""), "")
        self.assertEqual(telefone("123"), "123")


# Hash de senha rápido só nos testes (PBKDF2 é lento de propósito e dominava o tempo da suíte).
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Uma vez por classe: o hash de senha (PBKDF2) é o custo dominante da suíte.
        cls.admin = User.objects.create_superuser("admin", password="x")

    def setUp(self):
        self.client.force_login(self.admin)
        self.cliente = Cliente.objects.create(nome="Henrique", telefone="11943796788")
        self.veiculo = Veiculo.objects.create(placa="FIB3F99", modelo="Sportage", cliente=self.cliente)

    def post_os(self, url, itens=(), extra=None, n_itens_existentes=0):
        dados = {
            "cliente": self.cliente.pk, "veiculo": self.veiculo.pk, "relato_cliente": "Barulho na suspensão",
            "aberta_em_0": "15/10/2026", "aberta_em_1": "09:00:00",
            "itens-TOTAL_FORMS": len(itens), "itens-INITIAL_FORMS": n_itens_existentes,
            "aprovacoes-TOTAL_FORMS": 0, "aprovacoes-INITIAL_FORMS": 0,
            "historico-TOTAL_FORMS": 0, "historico-INITIAL_FORMS": 0,
        }
        for i, it in enumerate(itens):
            dados |= {f"itens-{i}-{k}": val for k, val in it.items()}
        return self.client.post(url, dados | (extra or {}))

    def test_paginas_principais_abrem(self):
        for nome in ("oficina_ordemservico", "oficina_cliente", "oficina_veiculo", "oficina_fornecedor"):
            for sufixo in ("changelist", "add"):
                with self.subTest(pagina=f"{nome}_{sufixo}"):
                    self.assertEqual(self.client.get(reverse(f"admin:{nome}_{sufixo}")).status_code, 200)

    def test_cadastro_de_cliente_com_mascara(self):
        resp = self.client.post(reverse("admin:oficina_cliente_add"), {
            "nome": "Maria", "telefone": "(11) 5555-1234", "documento": "529.982.247-25", "observacao": "",
            "veiculos-TOTAL_FORMS": 1, "veiculos-INITIAL_FORMS": 0,
            "veiculos-0-placa": "xyz-9876", "veiculos-0-marca": "", "veiculos-0-modelo": "", "veiculos-0-ano": "",
        })
        self.assertEqual(resp.status_code, 302)
        maria = Cliente.objects.get(nome="Maria")
        self.assertEqual((maria.telefone, maria.documento, maria.veiculos.get().placa),
                         ("1155551234", "52998224725", "XYZ9876"))

    def test_busca_os_por_placa(self):
        OrdemServico.objects.create(cliente=self.cliente, veiculo=self.veiculo, relato_cliente="x")
        resp = self.client.get(reverse("admin:oficina_ordemservico_changelist"), {"q": "FIB3F99"})
        self.assertContains(resp, "FIB3F99")

    def test_abrir_os_com_itens_e_aprovar(self):
        itens = [
            {"tipo": "peca", "descricao": "Braço suspensão", "quantidade": "2", "valor_unitario": "154,00",
             "origem": "fornecedor", "situacao": "ativo"},
            {"tipo": "servico", "descricao": "Suspensão traseira", "quantidade": "1", "valor_unitario": "600,00",
             "situacao": "ativo"},
        ]
        resp = self.post_os(reverse("admin:oficina_ordemservico_add"), itens)
        self.assertEqual(resp.status_code, 302, resp.content[:2000])
        os = OrdemServico.objects.get()
        self.assertEqual((os.numero, os.total()), (1, Decimal("908.00")))

        url = reverse("admin:oficina_ordemservico_change", args=[os.pk])
        ids = list(os.itens.values_list("pk", flat=True))
        existentes = [it | {"id": pk, "os": os.pk} for it, pk in zip(itens, ids)]
        resp = self.post_os(url, existentes, n_itens_existentes=2,
                            extra={"proximo_status": "aprovada", "canal": "whatsapp", "respondido_por": "Henrique"})
        self.assertEqual(resp.status_code, 302)
        os.refresh_from_db()
        self.assertEqual(os.status, S.APROVADA)
        self.assertEqual(os.aprovacoes.get().valor, Decimal("908.00"))

    def test_aprovacao_exige_canal_e_nome(self):
        os = OrdemServico.objects.create(cliente=self.cliente, veiculo=self.veiculo, relato_cliente="x")
        resp = self.post_os(reverse("admin:oficina_ordemservico_change", args=[os.pk]),
                            extra={"proximo_status": "aprovada"})
        self.assertEqual(resp.status_code, 200)  # volta ao formulário com erro
        self.assertContains(resp, "Obrigatório para registrar a resposta do cliente.")

    def test_proximo_passo_so_oferece_transicoes_validas(self):
        os = OrdemServico.objects.create(cliente=self.cliente, veiculo=self.veiculo, relato_cliente="x")
        resp = self.client.get(reverse("admin:oficina_ordemservico_change", args=[os.pk]))
        opcoes = [v for v, _ in resp.context["adminform"].form.fields["proximo_status"].choices]
        self.assertEqual(opcoes, ["", "aprovada", "recusada", "cancelada"])

    def test_aprovar_sem_itens_mostra_erro_e_nao_muda_status(self):
        os = OrdemServico.objects.create(cliente=self.cliente, veiculo=self.veiculo, relato_cliente="x")
        resp = self.post_os(reverse("admin:oficina_ordemservico_change", args=[os.pk]),
                            extra={"proximo_status": "aprovada", "canal": "presencial", "respondido_por": "H"})
        self.assertEqual(resp.status_code, 302)
        os.refresh_from_db()
        self.assertEqual(os.status, S.ORCAMENTO)
        mensagens = [str(m) for m in self.client.get(resp.url).context["messages"]]
        self.assertIn("O orçamento não tem itens.", mensagens)

    def test_exclusao_desabilitada(self):
        os = OrdemServico.objects.create(cliente=self.cliente, veiculo=self.veiculo, relato_cliente="x")
        resp = self.client.get(reverse("admin:oficina_ordemservico_delete", args=[os.pk]))
        self.assertEqual(resp.status_code, 403)
