"""O "Você sabia?" das telas de derrota e de vitória (J15, D35, C1, C7).

Os fatos ficam em `conteudo/pt_BR/fatos.toml`, cada um ligado a um chefe e com a fonte
obrigatória: sem fonte, o fato nem carrega. Os fatos vêm do João ou do grupo (D35). Para
um chefe sem fatos, sai uma **dica** sobre as regras do jogo, sem afirmar nada sobre o
mundo real.

O sorteio é por chefe e sem repetição: os fatos saem embaralhados (com semente, D23) até
acabar; a rodada seguinte não começa pelo último que saiu. Os fatos já vistos ficam
guardados para o save e o Caderno da Cooperativa (J16, J18).
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from enum import Enum
from functools import cache

from cupeco.dominio.chefe import listar_chefes
from cupeco.dominio.dados import DadosInvalidos, converter, ler_toml

MAXIMO_DE_FRASES = 2  # C7
MAXIMO_DE_CARACTERES = 220  # para caber na tela
FIM_DE_FRASE = re.compile(r"[.!?…]+(?=\s|$)")
DATA = re.compile(r"\d{4}-\d{2}-\d{2}")


class TipoFonte(Enum):
    """Fontes aceitas pela C1 (nunca livros)."""

    LEGISLACAO = "legislacao"
    ORGAO_OFICIAL = "orgao_oficial"
    ARTIGO_REVISADO = "artigo_revisado"
    INSTITUICAO_PESQUISA = "instituicao_pesquisa"


@dataclass(frozen=True)
class Fonte:
    titulo: str
    autor: str  # órgão, instituição ou autores
    ano: int
    tipo: TipoFonte
    consultado_em: str  # AAAA-MM-DD: quando a fonte foi conferida
    url: str | None = None


@dataclass(frozen=True)
class Fato:
    id: str
    chefe: str  # nome do arquivo em conteudo/chefes/, sem o .toml
    texto: str
    fonte: Fonte


@dataclass(frozen=True)
class Dica:
    id: str
    texto: str


@dataclass(frozen=True)
class TabelaFatos:
    dicas: tuple[Dica, ...]
    fatos: tuple[Fato, ...] = ()

    def fatos_de(self, chefe: str) -> tuple[Fato, ...]:
        return tuple(fato for fato in self.fatos if fato.chefe == chefe)


def contar_frases(texto: str) -> int:
    """Frases terminadas em ponto, exclamação ou reticências (um número como 12.305 não
    conta); um texto sem ponto final é uma frase."""
    return max(1, len(FIM_DE_FRASE.findall(texto.strip())))


def _validar_texto(texto: str, onde: str) -> None:
    if not texto.strip():
        raise DadosInvalidos(f"{onde}.texto: não pode ficar vazio")
    if contar_frases(texto) > MAXIMO_DE_FRASES:
        raise DadosInvalidos(f"{onde}.texto: no máximo {MAXIMO_DE_FRASES} frases (C7)")
    if len(texto) > MAXIMO_DE_CARACTERES:
        raise DadosInvalidos(f"{onde}.texto: no máximo {MAXIMO_DE_CARACTERES} caracteres")


def _validar_fonte(fonte: Fonte, onde: str) -> None:
    for nome in ("titulo", "autor"):
        if not getattr(fonte, nome).strip():
            raise DadosInvalidos(f"{onde}.fonte.{nome}: não pode ficar vazio (C1)")
    if not DATA.fullmatch(fonte.consultado_em):
        raise DadosInvalidos(f"{onde}.fonte.consultado_em: use AAAA-MM-DD")
    if not 0 < fonte.ano <= int(fonte.consultado_em[:4]):
        raise DadosInvalidos(f"{onde}.fonte.ano: precisa vir antes da consulta")
    if fonte.url is not None and not fonte.url.startswith(("https://", "http://")):
        raise DadosInvalidos(f"{onde}.fonte.url: precisa começar com https://")


def validar_fatos(tabela: TabelaFatos, chefes: tuple[str, ...]) -> TabelaFatos:
    if not tabela.dicas:
        raise DadosInvalidos("fatos.dicas: precisa de pelo menos uma dica")
    ids = [dica.id for dica in tabela.dicas] + [fato.id for fato in tabela.fatos]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    if repetidos:
        raise DadosInvalidos(f"fatos: id repetido: {', '.join(repetidos)}")
    for dica in tabela.dicas:
        _validar_texto(dica.texto, f"fatos.dicas.{dica.id}")
    for fato in tabela.fatos:
        onde = f"fatos.{fato.id}"
        if fato.chefe not in chefes:
            raise DadosInvalidos(f"{onde}.chefe: não existe o chefe {fato.chefe!r}")
        _validar_texto(fato.texto, onde)
        _validar_fonte(fato.fonte, onde)
    return tabela


@cache
def carregar_fatos() -> TabelaFatos:
    tabela = converter(ler_toml("pt_BR/fatos.toml"), TabelaFatos, "fatos")
    return validar_fatos(tabela, listar_chefes())


# --- sorteio -------------------------------------------------------------------------


@dataclass(frozen=True)
class Mensagem:
    """O que a tela mostra: um fato com fonte ("Você sabia?") ou uma dica do jogo."""

    id: str
    texto: str
    fonte: Fonte | None  # None nas dicas

    @property
    def e_fato(self) -> bool:
        return self.fonte is not None


DICAS = "dicas"  # chave do monte das dicas


class SorteioDeFatos:
    """Sorteia a mensagem de cada tela, por chefe, sem repetir até esgotar."""

    def __init__(self, tabela: TabelaFatos, sorteio: random.Random) -> None:
        self.tabela = tabela
        self._sorteio = sorteio
        self._montes: dict[str, list[Mensagem]] = {}
        self._ultima: dict[str, str] = {}
        self.vistos: dict[str, list[str]] = {}  # ids dos fatos já vistos, por chefe

    def _todas(self, chefe: str) -> tuple[str, list[Mensagem]]:
        fatos = self.tabela.fatos_de(chefe)
        if fatos:
            return chefe, [Mensagem(f.id, f.texto, f.fonte) for f in fatos]
        return DICAS, [Mensagem(d.id, d.texto, None) for d in self.tabela.dicas]

    def proxima(self, chefe: str) -> Mensagem:
        chave, todas = self._todas(chefe)
        monte = self._montes.get(chave)
        if not monte:
            monte = list(todas)
            self._sorteio.shuffle(monte)
            # A rodada nova não começa pela última mensagem da rodada anterior.
            if len(monte) > 1 and monte[0].id == self._ultima.get(chave):
                monte.append(monte.pop(0))
            self._montes[chave] = monte
        mensagem = monte.pop(0)
        self._ultima[chave] = mensagem.id
        if mensagem.e_fato:
            vistos = self.vistos.setdefault(chefe, [])
            if mensagem.id not in vistos:
                vistos.append(mensagem.id)
        return mensagem
