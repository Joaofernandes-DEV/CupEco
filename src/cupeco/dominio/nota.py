"""Nota da luta (J14, D32): função pura do desempenho, com as faixas em `conteudo/nota.toml`.

Só há nota na vitória. Os pontos vêm do tempo (faixas por chefe), da vida restante, das
triagens certas e dos Supers usados, cada um com seu máximo; a soma vira uma letra de A+ a
D. As triagens de outra cor não valem pontos. O modo fica registrado ao lado da nota, sem
teto no Simples (D13). Contas em inteiros (D23).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from itertools import pairwise

from cupeco.dominio.batalha import Batalha, Resultado
from cupeco.dominio.dados import DadosInvalidos, converter, ler_toml
from cupeco.dominio.jogador import carregar_parametros_jogador
from cupeco.dominio.modos import Modo


@dataclass(frozen=True)
class Letra:
    letra: str
    minimo: int


@dataclass(frozen=True)
class TemposChefe:
    chefe: str  # nome do arquivo em conteudo/chefes/, sem o .toml
    limites: tuple[int, ...]  # quadros: o fim de cada faixa de tempo


@dataclass(frozen=True)
class RegrasNota:
    pontos_tempo: tuple[int, ...]
    pontos_tempo_acima: int
    pontos_por_vida: int
    pontos_por_triagem: int
    maximo_triagens: int
    pontos_por_super: int
    maximo_supers: int
    tempos: tuple[TemposChefe, ...]
    letras: tuple[Letra, ...]

    def limites_de(self, chefe: str) -> tuple[int, ...]:
        for tempos in self.tempos:
            if tempos.chefe == chefe:
                return tempos.limites
        raise DadosInvalidos(f"nota.tempos: falta o chefe {chefe!r}")


def _decrescente(valores: tuple[int, ...]) -> bool:
    return all(a > b for a, b in pairwise(valores))


def validar_regras_nota(regras: RegrasNota, vida_maxima: int) -> RegrasNota:
    inteiros = (
        regras.pontos_por_vida,
        regras.pontos_por_triagem,
        regras.maximo_triagens,
        regras.pontos_por_super,
        regras.maximo_supers,
    )
    if min(inteiros) <= 0 or regras.pontos_tempo_acima < 0:
        raise DadosInvalidos("nota: pontos e máximos precisam ser positivos")
    pontos = (*regras.pontos_tempo, regras.pontos_tempo_acima)
    if not regras.pontos_tempo or not all(a >= b for a, b in pairwise(pontos)):
        raise DadosInvalidos("nota.pontos_tempo: do mais rápido ao mais lento, sem aumentar")
    nomes = [tempos.chefe for tempos in regras.tempos]
    if len(set(nomes)) != len(nomes):
        raise DadosInvalidos("nota.tempos: chefe repetido")
    for tempos in regras.tempos:
        limites = tempos.limites
        if len(limites) != len(regras.pontos_tempo):
            raise DadosInvalidos(
                f"nota.tempos.{tempos.chefe}: um limite para cada faixa de pontos_tempo"
            )
        if limites[0] <= 0 or not all(a < b for a, b in pairwise(limites)):
            raise DadosInvalidos(f"nota.tempos.{tempos.chefe}: limites positivos e crescentes")
    letras = regras.letras
    if not letras or len({letra.letra for letra in letras}) != len(letras):
        raise DadosInvalidos("nota.letras: letras sem repetição")
    if not _decrescente(tuple(letra.minimo for letra in letras)) or letras[-1].minimo != 0:
        raise DadosInvalidos("nota.letras: mínimos decrescentes, o último em 0")
    maximo = (
        regras.pontos_tempo[0]
        + vida_maxima * regras.pontos_por_vida
        + regras.maximo_triagens * regras.pontos_por_triagem
        + regras.maximo_supers * regras.pontos_por_super
    )
    if maximo < letras[0].minimo:
        raise DadosInvalidos(f"nota.letras: {letras[0].letra} exige mais que o máximo ({maximo})")
    return regras


@cache
def carregar_regras_nota() -> RegrasNota:
    regras = converter(ler_toml("nota.toml"), RegrasNota, "nota")
    return validar_regras_nota(regras, carregar_parametros_jogador().vida_maxima)


# --- a nota --------------------------------------------------------------------------


@dataclass(frozen=True)
class Desempenho:
    """O que conta para a nota de uma luta vencida."""

    chefe: str  # nome do arquivo em conteudo/chefes/
    quadros: int
    vida: int
    triagens_certas: int
    supers: int
    modo: Modo


@dataclass(frozen=True)
class Nota:
    letra: str
    pontos: int
    modo: Modo  # mostrado ao lado da nota (J14)
    pontos_tempo: int
    pontos_vida: int
    pontos_triagens: int
    pontos_super: int


def calcular_nota(desempenho: Desempenho, regras: RegrasNota | None = None) -> Nota:
    regras = regras or carregar_regras_nota()
    pontos_tempo = regras.pontos_tempo_acima
    for limite, pontos in zip(
        regras.limites_de(desempenho.chefe), regras.pontos_tempo, strict=True
    ):
        if desempenho.quadros <= limite:
            pontos_tempo = pontos
            break
    pontos_vida = desempenho.vida * regras.pontos_por_vida
    triagens = min(desempenho.triagens_certas, regras.maximo_triagens)
    pontos_triagens = triagens * regras.pontos_por_triagem
    pontos_super = min(desempenho.supers, regras.maximo_supers) * regras.pontos_por_super
    total = pontos_tempo + pontos_vida + pontos_triagens + pontos_super
    letra = next(letra.letra for letra in regras.letras if total >= letra.minimo)
    return Nota(
        letra, total, desempenho.modo, pontos_tempo, pontos_vida, pontos_triagens, pontos_super
    )


def desempenho_da(batalha: Batalha, chefe: str) -> Desempenho:
    """O desempenho de uma luta vencida; `chefe` é o nome do arquivo do chefe."""
    if batalha.resultado is not Resultado.VITORIA:
        raise ValueError("só há nota quando a luta termina em vitória")
    jogador = batalha.jogador
    return Desempenho(
        chefe=chefe,
        quadros=batalha.quadro,
        vida=jogador.vida,
        triagens_certas=jogador.estatisticas.triagens_certas,
        supers=jogador.estatisticas.supers,
        modo=batalha.modo,
    )
