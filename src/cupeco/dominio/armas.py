"""Armas do Canhão de Triagem e o arsenal da Dara (J2).

Cada arma tem a cor de um material reciclável, que é a "lixeira ativa" da Triagem (D12).
Os valores vêm de `conteudo/armas.toml` (D26). O custo do tiro EX no Medidor de Reciclagem
entra no PR da Triagem; aqui fica só a criação do projétil EX.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from cupeco.dominio.comandos import Direcao
from cupeco.dominio.dados import DadosInvalidos, converter, ler_toml
from cupeco.dominio.fisica import Caixa
from cupeco.dominio.materiais import Material
from cupeco.dominio.projeteis import VETORES, Dono, Projetil, tamanho_orientado

TOLERANCIA_UNITARIA = 1e-3


@dataclass(frozen=True)
class TiroEx:
    nome: str
    velocidade: float
    dano: int
    quadros_de_vida: int
    largura: float
    altura: float
    perfura: bool


@dataclass(frozen=True)
class Arma:
    nome: str
    material: Material
    quadros_entre_tiros: int
    velocidade: float
    dano: int
    quadros_de_vida: int
    largura: float
    altura: float
    espalhamento: tuple[tuple[float, float], ...]
    ex: TiroEx


def validar_arma(arma: Arma, onde: str) -> Arma:
    if not arma.material.separavel:
        raise DadosInvalidos(f"{onde}.material: a arma precisa ser de um material reciclável")
    numeros = {
        "quadros_entre_tiros": arma.quadros_entre_tiros,
        "velocidade": arma.velocidade,
        "dano": arma.dano,
        "quadros_de_vida": arma.quadros_de_vida,
        "largura": arma.largura,
        "altura": arma.altura,
        "ex.velocidade": arma.ex.velocidade,
        "ex.dano": arma.ex.dano,
        "ex.quadros_de_vida": arma.ex.quadros_de_vida,
        "ex.largura": arma.ex.largura,
        "ex.altura": arma.ex.altura,
    }
    for nome, valor in numeros.items():
        if valor <= 0:
            raise DadosInvalidos(f"{onde}.{nome}: precisa ser positivo, veio {valor}")
    if not arma.espalhamento:
        raise DadosInvalidos(f"{onde}.espalhamento: precisa de pelo menos um tiro")
    for indice, (c, s) in enumerate(arma.espalhamento):
        if abs(c * c + s * s - 1) > TOLERANCIA_UNITARIA:
            raise DadosInvalidos(
                f"{onde}.espalhamento[{indice}]: [cosseno, seno] precisa ter tamanho 1"
            )
    return arma


@cache
def carregar_armas() -> dict[Material, Arma]:
    bruto = ler_toml("armas.toml")
    armas = {}
    for chave, dados in bruto.items():
        arma = validar_arma(converter(dados, Arma, f"armas.{chave}"), f"armas.{chave}")
        if arma.material.value != chave:
            raise DadosInvalidos(f"armas.{chave}.material: precisa ser {chave!r}")
        armas[arma.material] = arma
    return armas


def boca_do_canhao(caixa: Caixa, mira: Direcao, distancia: float) -> tuple[float, float]:
    """Ponto de onde sai o tiro: o centro da caixa, avançado na direção da mira."""
    dx, dy = VETORES[mira]
    cx, cy = caixa.centro
    return (cx + dx * distancia, cy + dy * distancia)


def disparar(arma: Arma, origem: tuple[float, float], mira: Direcao) -> list[Projetil]:
    """Os projéteis de um disparo normal, um por item do espalhamento."""
    dx, dy = VETORES[mira]
    projeteis = []
    for c, s in arma.espalhamento:
        rx, ry = dx * c - dy * s, dx * s + dy * c
        largura, altura = tamanho_orientado(arma.largura, arma.altura, rx, ry)
        projeteis.append(
            Projetil(
                x=origem[0],
                y=origem[1],
                largura=largura,
                altura=altura,
                vx=rx * arma.velocidade,
                vy=ry * arma.velocidade,
                dano=arma.dano,
                quadros_de_vida=arma.quadros_de_vida,
                dono=Dono.JOGADOR,
                material=arma.material,
            )
        )
    return projeteis


def disparar_ex(arma: Arma, origem: tuple[float, float], mira: Direcao) -> Projetil:
    """O projétil do tiro EX da arma (o custo no Medidor é conferido por quem chama)."""
    ex = arma.ex
    dx, dy = VETORES[mira]
    largura, altura = tamanho_orientado(ex.largura, ex.altura, dx, dy)
    return Projetil(
        x=origem[0],
        y=origem[1],
        largura=largura,
        altura=altura,
        vx=dx * ex.velocidade,
        vy=dy * ex.velocidade,
        dano=ex.dano,
        quadros_de_vida=ex.quadros_de_vida,
        dono=Dono.JOGADOR,
        material=arma.material,
        perfura=ex.perfura,
        ex=True,
    )


class Arsenal:
    """As duas armas equipadas, qual está ativa e a cadência de tiro."""

    def __init__(self, armas: tuple[Arma, ...]) -> None:
        if not armas:
            raise ValueError("o arsenal precisa de pelo menos uma arma")
        self.armas = armas
        self.indice = 0
        self._espera = 0

    @classmethod
    def padrao(cls) -> Arsenal:
        """O arsenal da V1: Plástico e Papel (D6)."""
        armas = carregar_armas()
        return cls((armas[Material.PLASTICO], armas[Material.PAPEL]))

    @property
    def ativa(self) -> Arma:
        return self.armas[self.indice]

    def trocar(self) -> None:
        self.indice = (self.indice + 1) % len(self.armas)

    def atualizar(
        self, atirando: bool, origem: tuple[float, float], mira: Direcao
    ) -> list[Projetil]:
        """Um passo: com o tiro segurado, dispara sempre que a cadência permitir."""
        if self._espera > 0:
            self._espera -= 1
        if not atirando or self._espera > 0:
            return []
        self._espera = self.ativa.quadros_entre_tiros
        return disparar(self.ativa, origem, mira)
