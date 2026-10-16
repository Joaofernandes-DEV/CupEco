"""Chefes (D28): vida em pontos inteiros, fases por limite de vida e transição invulnerável.

Cada fase começa quando a vida cai até uma porcentagem da vida máxima (a primeira em 100%).
Um dano grande nunca pula uma fase: a vida para no limite da fase seguinte e a transição
começa, para que todo jogador veja as 3 fases de cada chefe (no espírito da D13).

O chefe se move por uma rota de pontos (o centro da caixa vai de um ponto ao outro, em
velocidade constante, e volta ao primeiro) e ataca com o roteiro da fase (`ataques.py`):
os ataques param durante a transição e recomeçam com a lista da fase nova.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum
from itertools import pairwise

from cupeco.dominio.ataques import (
    AVISO_MINIMO_NORMAL,
    DadosAtaque,
    Etapa,
    Inimigo,
    Roteiro,
    validar_ataque,
)
from cupeco.dominio.dados import DadosInvalidos, converter, ler_toml
from cupeco.dominio.fisica import Caixa
from cupeco.dominio.projeteis import Projetil

Ponto = tuple[float, float]


class EventoChefe(Enum):
    LEVOU_DANO = "chefe_levou_dano"
    MUDOU_FASE = "chefe_mudou_fase"
    TERMINOU_TRANSICAO = "chefe_terminou_transicao"
    DERROTADO = "chefe_derrotado"
    ATAQUE_AVISO = "ataque_aviso"  # começou o aviso de um ataque (som e desenho do alerta)
    ATAQUE_ATIVO = "ataque_ativo"


@dataclass(frozen=True)
class DadosFase:
    nome: str
    comeca_em: int  # porcentagem da vida máxima em que a fase começa (a primeira: 100)
    largura: float
    altura: float
    rota: tuple[Ponto, ...]
    velocidade: float
    ataques: tuple[DadosAtaque, ...] = ()


@dataclass(frozen=True)
class DadosChefe:
    nome: str
    vida: int
    quadros_transicao: int
    dano_por_contato: bool
    fases: tuple[DadosFase, ...]


def validar_chefe(
    dados: DadosChefe, onde: str, aviso_minimo: int = AVISO_MINIMO_NORMAL
) -> DadosChefe:
    """Confere o chefe; `aviso_minimo` é o do modo da luta (`modos.py`)."""
    if dados.vida <= 0:
        raise DadosInvalidos(f"{onde}.vida: precisa ser positiva")
    if dados.quadros_transicao <= 0:
        raise DadosInvalidos(f"{onde}.quadros_transicao: precisa ser positivo")
    if not dados.fases:
        raise DadosInvalidos(f"{onde}.fases: precisa de pelo menos uma fase")
    if dados.fases[0].comeca_em != 100:
        raise DadosInvalidos(f"{onde}.fases[0].comeca_em: a primeira fase começa em 100")
    for indice, (anterior, fase) in enumerate(pairwise(dados.fases), start=1):
        if not 0 < fase.comeca_em < anterior.comeca_em:
            raise DadosInvalidos(
                f"{onde}.fases[{indice}].comeca_em: precisa ficar entre 0 e a fase anterior"
            )
    for indice, fase in enumerate(dados.fases):
        if dados.vida * fase.comeca_em // 100 < 1:
            raise DadosInvalidos(f"{onde}.fases[{indice}].comeca_em: vida pequena demais")
        if fase.largura <= 0 or fase.altura <= 0 or fase.velocidade < 0:
            raise DadosInvalidos(f"{onde}.fases[{indice}]: tamanho e velocidade inválidos")
        if not fase.rota:
            raise DadosInvalidos(f"{onde}.fases[{indice}].rota: precisa de pelo menos um ponto")
        for numero, ataque in enumerate(fase.ataques):
            validar_ataque(ataque, f"{onde}.fases[{indice}].ataques[{numero}]", aviso_minimo)
    return dados


def carregar_chefe(nome: str) -> DadosChefe:
    onde = f"chefes.{nome}"
    return validar_chefe(converter(ler_toml(f"chefes/{nome}.toml"), DadosChefe, onde), onde)


class Chefe:
    """Um chefe em luta. `x` e `y` são o centro da caixa."""

    def __init__(self, dados: DadosChefe, sorteio: random.Random | None = None) -> None:
        self.dados = dados
        self._sorteio = sorteio or random.Random(0)
        self.roteiro = Roteiro(dados.fases[0].ataques, self._sorteio)
        self.novos_projeteis: list[Projetil] = []
        self.novos_inimigos: list[Inimigo] = []
        self.nome = dados.nome
        self.vida = dados.vida
        self.fase = 0
        self._transicao = 0
        rota = dados.fases[0].rota
        self.x, self.y = rota[0]
        # Já começa no primeiro ponto: o próximo destino é o segundo.
        self._alvo_da_rota = 1 % len(rota)

    # --- consultas ------------------------------------------------------------------

    @property
    def dados_da_fase(self) -> DadosFase:
        return self.dados.fases[self.fase]

    @property
    def caixa(self) -> Caixa:
        fase = self.dados_da_fase
        return Caixa(self.x - fase.largura / 2, self.y - fase.altura / 2, fase.largura, fase.altura)

    @property
    def derrotado(self) -> bool:
        return self.vida == 0

    @property
    def em_transicao(self) -> bool:
        return self._transicao > 0

    @property
    def vulneravel(self) -> bool:
        return not self.derrotado and not self.em_transicao

    def limite_da_fase(self, indice: int) -> int:
        """Vida em que a fase `indice` começa."""
        return self.dados.vida * self.dados.fases[indice].comeca_em // 100

    @property
    def progresso(self) -> float:
        """Quanto da vida já foi tirada, de 0 a 1 (para a barra da tela de derrota, I6)."""
        return 1 - self.vida / self.dados.vida

    @property
    def marcos(self) -> tuple[float, ...]:
        """Onde começam as fases 2 em diante, na mesma escala do progresso."""
        return tuple(1 - fase.comeca_em / 100 for fase in self.dados.fases[1:])

    # --- passo ----------------------------------------------------------------------

    @property
    def zona_ativa(self) -> Caixa | None:
        return self.roteiro.zona_ativa

    @property
    def zona_avisada(self) -> Caixa | None:
        return self.roteiro.zona_avisada

    @property
    def em_aviso(self) -> bool:
        return self.roteiro.atual is not None and self.roteiro.etapa is Etapa.AVISO

    def atualizar(self, alvo: Ponto | None = None) -> list[EventoChefe]:
        """Um passo. `alvo` é o centro da Dara (para os tiros mirados e os inimigos)."""
        eventos = []
        self.novos_projeteis, self.novos_inimigos = [], []
        if self._transicao > 0:
            self._transicao -= 1
            if self._transicao == 0:
                eventos.append(EventoChefe.TERMINOU_TRANSICAO)
        if self.derrotado:
            return eventos
        self._andar()
        if self._transicao == 0:
            disparo, comecos = self.roteiro.atualizar((self.x, self.y), alvo or (self.x, self.y))
            self.novos_projeteis, self.novos_inimigos = disparo.projeteis, disparo.inimigos
            if Etapa.AVISO.value in comecos:
                eventos.append(EventoChefe.ATAQUE_AVISO)
            if Etapa.ATIVO.value in comecos:
                eventos.append(EventoChefe.ATAQUE_ATIVO)
        return eventos

    def _andar(self) -> None:
        fase = self.dados_da_fase
        destino = fase.rota[self._alvo_da_rota % len(fase.rota)]
        dx, dy = destino[0] - self.x, destino[1] - self.y
        distancia = math.sqrt(dx * dx + dy * dy)
        if distancia <= fase.velocidade:
            self.x, self.y = destino
            self._alvo_da_rota = (self._alvo_da_rota + 1) % len(fase.rota)
        else:
            self.x += dx / distancia * fase.velocidade
            self.y += dy / distancia * fase.velocidade

    def levar_dano(self, dano: int) -> list[EventoChefe]:
        """Aplica dano; durante a transição ou depois de derrotado, nada acontece."""
        if not self.vulneravel or dano <= 0:
            return []
        eventos = [EventoChefe.LEVOU_DANO]
        proxima = self.fase + 1
        piso = self.limite_da_fase(proxima) if proxima < len(self.dados.fases) else 0
        self.vida = max(piso, self.vida - dano)
        if self.vida == 0:
            self.roteiro.interromper()
            eventos.append(EventoChefe.DERROTADO)
        elif proxima < len(self.dados.fases) and self.vida <= piso:
            self.fase = proxima
            self._transicao = self.dados.quadros_transicao
            self._alvo_da_rota = 0
            self.roteiro = Roteiro(self.dados.fases[proxima].ataques, self._sorteio)
            eventos.append(EventoChefe.MUDOU_FASE)
        return eventos
