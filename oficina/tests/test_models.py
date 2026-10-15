from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from oficina.models import Aprovacao, Cliente, Contador, Fornecedor, ItemOS, OrdemServico, Veiculo

S = OrdemServico.Status


def criar_os(**kwargs):
    cliente = kwargs.pop("cliente", None) or Cliente.objects.create(nome="Henrique")
    veiculo = kwargs.pop("veiculo", None) or Veiculo.objects.create(
        placa=f"ABC1D{Veiculo.objects.count():02d}", cliente=cliente
    )
    return OrdemServico.objects.create(cliente=cliente, veiculo=veiculo, relato_cliente="Barulho", **kwargs)


def item(os, **kwargs):
    dados = {"tipo": "servico", "descricao": "Mão de obra", "valor_unitario": Decimal("100")} | kwargs
    obj = ItemOS(os=os, **dados)
    obj.full_clean()
    obj.save()
    return obj


class ClienteTests(TestCase):
    def test_normaliza_documento_e_telefone(self):
        c = Cliente.objects.create(nome="A", documento="529.982.247-25", telefone="(11) 94379-6788")
        self.assertEqual((c.documento, c.telefone), ("52998224725", "11943796788"))

    def test_full_clean_aceita_entrada_com_mascara(self):
        # Regressão: o tamanho máximo era checado antes de normalizar a máscara.
        c = Cliente(nome="A", documento="12.ABC.345/01DE-35", telefone="(11) 94379-6788")
        c.full_clean()
        self.assertEqual((c.documento, c.telefone), ("12ABC34501DE35", "11943796788"))
        veiculo = Veiculo(placa="abc-1234", cliente=Cliente.objects.create(nome="B"))
        veiculo.full_clean()
        self.assertEqual(veiculo.placa, "ABC1234")

    def test_documento_invalido_e_rejeitado(self):
        with self.assertRaises(ValidationError):
            Cliente(nome="A", documento="111.111.111-11").full_clean()

    def test_documento_unico_mas_vazio_pode_repetir(self):
        Cliente.objects.create(nome="A")
        Cliente.objects.create(nome="B")  # dois sem documento: ok
        Cliente.objects.create(nome="C", documento="52998224725")
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(nome="D", documento="529.982.247-25")

    def test_nao_apaga_cliente_com_veiculo(self):
        c = Cliente.objects.create(nome="A")
        Veiculo.objects.create(placa="ABC1234", cliente=c)
        with self.assertRaises(ProtectedError):
            c.delete()


class VeiculoTests(TestCase):
    def test_placa_normalizada_e_unica(self):
        c = Cliente.objects.create(nome="A")
        self.assertEqual(Veiculo.objects.create(placa="fib-3f99", cliente=c).placa, "FIB3F99")
        with self.assertRaises(IntegrityError):
            Veiculo.objects.create(placa="FIB3F99", cliente=c)

    def test_ano_fora_da_faixa_viola_constraint(self):
        c = Cliente.objects.create(nome="A")
        with self.assertRaises(IntegrityError):
            Veiculo.objects.create(placa="ABC1234", cliente=c, ano=1800)


class NumeracaoTests(TestCase):
    def test_numeros_sequenciais_sem_buracos(self):
        numeros = [criar_os().numero for _ in range(3)]
        self.assertEqual(numeros, [1, 2, 3])

    def test_rollback_nao_consome_numero(self):
        criar_os()
        try:
            with transaction.atomic():
                Contador.proximo("os")
                raise RuntimeError
        except RuntimeError:
            pass
        self.assertEqual(criar_os().numero, 2)

    def test_salvar_de_novo_mantem_numero(self):
        os = criar_os()
        os.diagnostico = "Bucha gasta"
        os.save()
        self.assertEqual(os.numero, 1)


class OrdemServicoTests(TestCase):
    def test_veiculo_de_outro_cliente_e_rejeitado(self):
        outro = Veiculo.objects.create(placa="XYZ9876", cliente=Cliente.objects.create(nome="Outro"))
        os = OrdemServico(cliente=Cliente.objects.create(nome="A"), veiculo=outro, relato_cliente="x")
        with self.assertRaises(ValidationError):
            os.clean()

    def test_fluxo_completo_registra_historico(self):
        os = criar_os()
        item(os)
        os.registrar_decisao(Aprovacao.Decisao.APROVADO, Aprovacao.Canal.WHATSAPP, "Henrique")
        os.alterar_status(S.EM_EXECUCAO)
        os.alterar_status(S.PRONTA)
        os.forma_pagamento = OrdemServico.FormaPagamento.PIX
        os.alterar_status(S.ENTREGUE)
        os.refresh_from_db()
        self.assertEqual(os.status, S.ENTREGUE)
        self.assertIsNotNone(os.entregue_em)
        self.assertEqual(
            list(os.historico.values_list("para", flat=True)), ["aprovada", "em_execucao", "pronta", "entregue"]
        )

    def test_transicao_invalida_e_bloqueada(self):
        os = criar_os()
        for destino in (S.EM_EXECUCAO, S.PRONTA, S.ENTREGUE):
            with self.subTest(destino=destino), self.assertRaises(ValidationError):
                os.alterar_status(destino)
        self.assertEqual(os.status, S.ORCAMENTO)

    def test_entrega_exige_forma_de_pagamento(self):
        os = criar_os()
        item(os)
        os.registrar_decisao("aprovado", "presencial", "H")
        os.alterar_status(S.EM_EXECUCAO)
        os.alterar_status(S.PRONTA)
        with self.assertRaises(ValidationError):
            os.alterar_status(S.ENTREGUE)

    def test_aprovacao_guarda_valor_e_exige_itens(self):
        os = criar_os()
        with self.assertRaises(ValidationError):
            os.registrar_decisao("aprovado", "telefone", "H")
        item(os, valor_unitario=Decimal("4526.00"))
        aprovacao = os.registrar_decisao("aprovado", "telefone", "H")
        self.assertEqual(aprovacao.valor, Decimal("4526.00"))
        self.assertEqual(os.status, S.APROVADA)

    def test_recusa_e_reconsideracao(self):
        os = criar_os()
        item(os)
        os.registrar_decisao("recusado", "presencial", "H")
        self.assertEqual(os.status, S.RECUSADA)
        os.alterar_status(S.ORCAMENTO, motivo="Cliente reconsiderou")
        self.assertEqual(os.status, S.ORCAMENTO)


class TotaisTests(TestCase):
    def test_soma_pecas_e_servicos_e_ignora_devolvidos(self):
        os = criar_os()
        primo = Fornecedor.objects.create(nome="Primo")
        item(os, tipo="peca", descricao="Braço", quantidade=Decimal("2"), valor_unitario=Decimal("154.00"),
             origem="fornecedor", fornecedor=primo)
        item(os, tipo="peca", descricao="Disco errado", valor_unitario=Decimal("600.00"), origem="fornecedor",
             situacao="devolvido")
        item(os, descricao="Suspensão", valor_unitario=Decimal("500.00"))
        self.assertEqual(os.total("peca"), Decimal("308.00"))
        self.assertEqual(os.total("servico"), Decimal("500.00"))
        self.assertEqual(os.total(), Decimal("808.00"))

    def test_quantidade_fracionada_arredonda_em_centavos(self):
        os = criar_os()
        i = item(os, tipo="peca", descricao="Óleo (L)", quantidade=Decimal("3.5"),
                 valor_unitario=Decimal("39.99"), origem="fornecedor")
        self.assertEqual(i.valor_total, Decimal("139.97"))  # 139.965 → 139.97


class ItemTests(TestCase):
    def test_servico_nao_tem_origem(self):
        i = item(criar_os(), origem="fornecedor")
        self.assertEqual(i.origem, "")

    def test_peca_exige_origem(self):
        with self.assertRaises(ValidationError):
            item(criar_os(), tipo="peca", descricao="Batente")

    def test_peca_do_cliente_nao_e_cobrada(self):
        primo = Fornecedor.objects.create(nome="Primo")
        i = item(criar_os(), tipo="peca", descricao="Kit amortecedor", origem="cliente",
                 valor_unitario=Decimal("900"), fornecedor=primo)
        self.assertEqual((i.valor_unitario, i.fornecedor), (Decimal("0"), None))

    def test_banco_barra_peca_do_cliente_com_valor(self):
        # Defesa em profundidade: mesmo pulando o clean(), o CHECK do banco barra.
        with self.assertRaises(IntegrityError):
            ItemOS.objects.create(os=criar_os(), tipo="peca", descricao="x", origem="cliente",
                                  valor_unitario=Decimal("10"))

    def test_os_pronta_bloqueia_alteracao_mas_permite_devolucao(self):
        os = criar_os()
        i = item(os, tipo="peca", descricao="Disco", valor_unitario=Decimal("600"), origem="fornecedor")
        os.registrar_decisao("aprovado", "presencial", "H")
        os.alterar_status(S.EM_EXECUCAO)
        os.alterar_status(S.PRONTA)
        i.valor_unitario = Decimal("1")
        with self.assertRaises(ValidationError):
            i.full_clean()
        i.refresh_from_db()
        i.situacao = ItemOS.Situacao.DEVOLVIDO
        i.full_clean()  # devolução é permitida
        with self.assertRaises(ValidationError):
            item(os, descricao="Serviço extra")

    def test_item_nao_pode_ser_apagado_com_historico(self):
        os = criar_os()
        item(os)
        with self.assertRaises(ProtectedError):
            os.delete()
