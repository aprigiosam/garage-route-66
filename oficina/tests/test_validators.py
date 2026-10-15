from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from oficina import validators as v


class CPFTests(SimpleTestCase):
    def test_aceita_com_e_sem_mascara(self):
        for cpf in ("529.982.247-25", "52998224725"):
            v.validar_cpf(cpf)

    def test_rejeita_invalidos(self):
        for cpf in ("529.982.247-26", "111.111.111-11", "123", ""):
            with self.subTest(cpf=cpf), self.assertRaises(ValidationError):
                v.validar_cpf(cpf)

    def test_normaliza_para_digitos(self):
        self.assertEqual(v.normalizar_cpf("529.982.247-25"), "52998224725")


class CNPJTests(SimpleTestCase):
    def test_aceita_numerico_e_alfanumerico(self):
        # 12.ABC.345/01DE-35 é o exemplo oficial da Receita para o CNPJ alfanumérico.
        for cnpj in ("11.222.333/0001-81", "12.ABC.345/01DE-35", "12abc34501de35"):
            with self.subTest(cnpj=cnpj):
                v.validar_cnpj(cnpj)

    def test_rejeita_invalidos(self):
        for cnpj in ("11.222.333/0001-82", "12.ABC.345/01DE-36", "00000000000000", "12ABC34501DEAB", ""):
            with self.subTest(cnpj=cnpj), self.assertRaises(ValidationError):
                v.validar_cnpj(cnpj)

    def test_normaliza_maiusculo_sem_mascara(self):
        self.assertEqual(v.normalizar_cnpj("12.abc.345/01de-35"), "12ABC34501DE35")


class PlacaTests(SimpleTestCase):
    def test_aceita_antiga_e_mercosul(self):
        for placa in ("ABC-1234", "abc1234", "ABC1D23", " fib3f99 "):
            with self.subTest(placa=placa):
                v.validar_placa(placa)

    def test_rejeita_invalidas(self):
        for placa in ("AB1234", "ABCD123", "1BC1234", "ABC12345", ""):
            with self.subTest(placa=placa), self.assertRaises(ValidationError):
                v.validar_placa(placa)

    def test_normaliza(self):
        self.assertEqual(v.normalizar_placa("abc-1d23"), "ABC1D23")


class TelefoneTests(SimpleTestCase):
    def test_aceita_celular_e_fixo(self):
        for tel in ("(11) 94379-6788", "11943796788", "(11) 5555-1234"):
            with self.subTest(tel=tel):
                v.validar_telefone(tel)

    def test_rejeita_invalidos(self):
        # curto, longo, DDD começando com 0, celular de 11 dígitos sem o 9
        for tel in ("94379-6788", "119437967881", "01943796788", "11843796788", ""):
            with self.subTest(tel=tel), self.assertRaises(ValidationError):
                v.validar_telefone(tel)

    def test_normaliza_para_digitos(self):
        self.assertEqual(v.normalizar_telefone("(11) 94379-6788"), "11943796788")
