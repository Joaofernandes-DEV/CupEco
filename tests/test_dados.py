from dataclasses import dataclass
from enum import Enum

import pytest

from cupeco.dominio.dados import DadosInvalidos, converter, ler_toml


@dataclass(frozen=True)
class Pulo:
    altura: float
    quadros: int


@dataclass(frozen=True)
class Exemplo:
    nome: str
    ativo: bool
    cor: tuple[int, int, int]
    pulo: Pulo
    passos: tuple[int, ...] = ()


VALIDO = {
    "nome": "Dara",
    "ativo": True,
    "cor": [1, 2, 3],
    "pulo": {"altura": 120, "quadros": 18},
    "passos": [1, 2, 3, 4],
}


def test_converte_tabela_valida_com_aninhamento():
    exemplo = converter(VALIDO, Exemplo, "exemplo")
    assert exemplo == Exemplo("Dara", True, (1, 2, 3), Pulo(120.0, 18), (1, 2, 3, 4))
    assert isinstance(exemplo.pulo.altura, float)


def test_valor_padrao_pode_faltar():
    sem_passos = {chave: valor for chave, valor in VALIDO.items() if chave != "passos"}
    assert converter(sem_passos, Exemplo, "exemplo").passos == ()


@pytest.mark.parametrize(
    ("alteracao", "mensagem"),
    [
        ({"velocidade": 3}, "exemplo: chave desconhecida: velocidade"),
        ({"pulo": {"altura": 120, "quadros": 18, "atlura": 1}}, "exemplo.pulo: chave desconhecida"),
        ({"pulo": {"altura": 120}}, "exemplo.pulo: falta a chave quadros"),
        ({"nome": 7}, "exemplo.nome: esperava um texto"),
        ({"ativo": 1}, "exemplo.ativo: esperava verdadeiro ou falso"),
        ({"pulo": {"altura": 120, "quadros": 18.5}}, "exemplo.pulo.quadros: esperava um número"),
        ({"pulo": {"altura": True, "quadros": 18}}, "exemplo.pulo.altura: esperava um número"),
        ({"cor": [1, 2]}, "exemplo.cor: esperava 3 itens"),
        ({"cor": [1, 2, "3"]}, "exemplo.cor[2]: esperava um número inteiro"),
        ({"passos": "1,2"}, "exemplo.passos: esperava uma lista"),
    ],
)
def test_erros_dizem_onde_esta_o_problema(alteracao, mensagem):
    with pytest.raises(DadosInvalidos, match=mensagem.replace("[", r"\[").replace("]", r"\]")):
        converter({**VALIDO, **alteracao}, Exemplo, "exemplo")


def test_falta_chave_obrigatoria_no_topo():
    with pytest.raises(DadosInvalidos, match="exemplo: falta a chave pulo"):
        converter({chave: v for chave, v in VALIDO.items() if chave != "pulo"}, Exemplo, "exemplo")


def test_le_toml_do_pacote_de_conteudo():
    assert "fonte" in ler_toml("materiais.toml")


class Cor(Enum):
    AZUL = "azul"
    VERDE = "verde"


@dataclass(frozen=True)
class ComCor:
    cor: Cor


def test_converte_enumeracao_pelo_valor():
    assert converter({"cor": "verde"}, ComCor, "x") == ComCor(Cor.VERDE)


def test_valor_fora_da_enumeracao_e_erro():
    with pytest.raises(DadosInvalidos, match="x.cor: 'roxo' não é um de azul, verde"):
        converter({"cor": "roxo"}, ComCor, "x")
