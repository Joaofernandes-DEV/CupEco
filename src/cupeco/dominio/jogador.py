"""A Dara: movimento, pulo, dash, agachar, travar e mira (J1, D14).

Tudo avança em passos fixos (D8) a partir dos botões segurados (D24); os valores vêm de
`conteudo/jogador.toml` (D26). Tiro, Triagem e dano entram nos próximos PRs da Fase 1.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields
from enum import Enum
from functools import cache

from cupeco.dominio.comandos import Botao, Comandos, Controle, Direcao
from cupeco.dominio.dados import DadosInvalidos, converter, ler_toml
from cupeco.dominio.fisica import Corpo, Plataforma, apoios, mover

MUITO_TEMPO = 1_000_000  # "faz muito tempo" para os contadores de quadros


class Estado(Enum):
    PARADA = "parada"
    CORRENDO = "correndo"
    AGACHADA = "agachada"
    TRAVADA = "travada"
    NO_AR = "no_ar"
    DASH = "dash"


class EventoJogador(Enum):
    """Acontecimentos de um passo, para a interface tocar sons e animações."""

    PULOU = "pulou"
    POUSOU = "pousou"
    DASH = "dash"
    DESCEU = "desceu"


@dataclass(frozen=True)
class ParametrosJogador:
    largura: float
    altura: float
    altura_agachada: float
    velocidade_corrida: float
    gravidade: float
    queda_maxima: float
    velocidade_pulo: float
    corte_pulo: float
    quadros_tolerancia_beirada: int
    quadros_pulo_guardado: int
    velocidade_dash: float
    quadros_dash: int
    quadros_espera_dash: int
    quadros_descer: int


def validar_parametros(p: ParametrosJogador) -> ParametrosJogador:
    for campo in fields(p):
        valor = getattr(p, campo.name)
        if valor < 0 or (valor == 0 and campo.name != "quadros_espera_dash"):
            raise DadosInvalidos(f"jogador.{campo.name}: precisa ser positivo, veio {valor}")
    if p.altura_agachada >= p.altura:
        raise DadosInvalidos("jogador.altura_agachada: precisa ser menor que a altura")
    if p.corte_pulo > 1:
        raise DadosInvalidos("jogador.corte_pulo: vai de 0 a 1")
    return p


@cache
def carregar_parametros_jogador() -> ParametrosJogador:
    return validar_parametros(converter(ler_toml("jogador.toml"), ParametrosJogador, "jogador"))


class Jogador:
    """A Dara. `x` é a borda esquerda da caixa e `base` a altura dos pés."""

    def __init__(self, x: float, base: float, parametros: ParametrosJogador | None = None):
        self.p = parametros or carregar_parametros_jogador()
        self.corpo = Corpo(x, base - self.p.altura, self.p.largura, self.p.altura)
        self.controle = Controle()
        self.virada = 1  # 1 = olhando para a direita, -1 = para a esquerda
        self.estado = Estado.NO_AR
        self.mira: Direcao = (1, 0)
        self._desde_o_chao = MUITO_TEMPO
        self._pulo_guardado = 0
        self._pulo_cortavel = False
        self._dash_restante = 0
        self._dash_direcao = 1
        self._espera_dash = 0
        self._dash_aereo = True
        self._descer = 0
        self._agachada = False

    # --- postura --------------------------------------------------------------------

    def _mudar_altura(self, altura: float) -> None:
        """Muda a altura da caixa mantendo os pés no lugar."""
        base = self.corpo.y + self.corpo.altura
        self.corpo.altura = altura
        self.corpo.y = base - altura

    def _agachar(self) -> None:
        if not self._agachada:
            self._agachada = True
            self._mudar_altura(self.p.altura_agachada)

    def _ficar_em_pe(self) -> None:
        if self._agachada:
            self._agachada = False
            self._mudar_altura(self.p.altura)

    # --- passo ----------------------------------------------------------------------

    def atualizar(
        self, segurados: Comandos, plataformas: Iterable[Plataforma]
    ) -> list[EventoJogador]:
        """Avança um passo de 1/60 s e devolve os eventos que aconteceram."""
        p, corpo, controle = self.p, self.corpo, self.controle
        plataformas = list(plataformas)
        controle.atualizar(segurados)
        eventos: list[EventoJogador] = []
        estava_no_chao = corpo.no_chao

        if controle.apertou(Botao.PULO):
            self._pulo_guardado = p.quadros_pulo_guardado
        elif self._pulo_guardado > 0:
            self._pulo_guardado -= 1
        if self._espera_dash > 0:
            self._espera_dash -= 1
        if self._descer > 0:
            self._descer -= 1
        travada = corpo.no_chao and controle.segurando(Botao.TRAVAR)

        livre_para_dash = self._dash_restante == 0 and self._espera_dash == 0
        pode_dash = livre_para_dash and (corpo.no_chao or self._dash_aereo)
        if pode_dash and controle.apertou(Botao.DASH):
            self._iniciar_dash()
            eventos.append(EventoJogador.DASH)

        em_dash = self._dash_restante > 0
        if em_dash:
            self._passo_de_dash(plataformas)
        else:
            eventos.extend(self._passo_normal(plataformas, travada))

        if corpo.no_chao:
            self._desde_o_chao = 0
            self._dash_aereo = True
            if not estava_no_chao:
                eventos.append(EventoJogador.POUSOU)
        elif self._desde_o_chao < MUITO_TEMPO:
            self._desde_o_chao += 1

        self._atualizar_estado_e_mira(travada, em_dash)
        return eventos

    def _iniciar_dash(self) -> None:
        self._dash_restante = self.p.quadros_dash
        self._dash_direcao = self.controle.horizontal or self.virada
        self.virada = self._dash_direcao
        if not self.corpo.no_chao:
            self._dash_aereo = False
        self._pulo_cortavel = False
        self._ficar_em_pe()

    def _passo_de_dash(self, plataformas: list[Plataforma]) -> None:
        """Dash: velocidade fixa na horizontal, sem gravidade (D14: sem invencibilidade)."""
        corpo = self.corpo
        self._dash_restante -= 1
        if self._dash_restante == 0:
            self._espera_dash = self.p.quadros_espera_dash
        corpo.vx = self._dash_direcao * self.p.velocidade_dash
        corpo.vy = 0.0
        mover(corpo, plataformas, 0.0, self.p.queda_maxima)
        # Sem gravidade não há pouso; o apoio é conferido direto (sair da beirada no dash).
        corpo.no_chao = bool(apoios(corpo.caixa, plataformas))

    def _passo_normal(self, plataformas: list[Plataforma], travada: bool) -> list[EventoJogador]:
        p, corpo, controle = self.p, self.corpo, self.controle
        eventos = []

        agachar = corpo.no_chao and controle.segurando(Botao.BAIXO) and not travada
        if agachar:
            self._agachar()
        else:
            self._ficar_em_pe()

        corpo.vx = 0.0 if agachar or travada else controle.horizontal * p.velocidade_corrida
        if controle.horizontal and not travada:
            self.virada = controle.horizontal

        perto_do_chao = corpo.no_chao or self._desde_o_chao <= p.quadros_tolerancia_beirada
        if self._pulo_guardado > 0 and perto_do_chao:
            self._pulo_guardado = 0
            sobre_tabua = any(
                plataforma.atravessavel for plataforma in apoios(corpo.caixa, plataformas)
            )
            if corpo.no_chao and controle.segurando(Botao.BAIXO) and sobre_tabua:
                self._descer = p.quadros_descer
                eventos.append(EventoJogador.DESCEU)
            else:
                self._ficar_em_pe()
                corpo.vy = -p.velocidade_pulo
                self._pulo_cortavel = True
                self._desde_o_chao = MUITO_TEMPO
                eventos.append(EventoJogador.PULOU)

        # Pulo de altura variável: soltar o botão enquanto sobe corta a subida.
        if self._pulo_cortavel and corpo.vy < 0 and not controle.segurando(Botao.PULO):
            corpo.vy *= p.corte_pulo
            self._pulo_cortavel = False
        if corpo.vy >= 0:
            self._pulo_cortavel = False

        mover(corpo, plataformas, p.gravidade, p.queda_maxima, descer=self._descer > 0)
        return eventos

    def _atualizar_estado_e_mira(self, travada: bool, em_dash: bool) -> None:
        """`em_dash`: o passo foi de dash (inclusive o último, quando o contador zera)."""
        corpo = self.corpo
        h, v = self.controle.direcao
        frente: Direcao = (self.virada, 0)

        if em_dash:
            self.estado, self.mira = Estado.DASH, frente
        elif not corpo.no_chao:
            self.estado = Estado.NO_AR
            self.mira = (h, v) if (h or v) else frente
        elif travada:
            self.estado = Estado.TRAVADA
            if h:
                self.virada = h
            if (h, v) == (0, 0):
                self.mira = (self.virada, 0)
            elif (h, v) == (0, 1):
                self.mira = (self.virada, 1)  # no chão não se mira reto para baixo
            else:
                self.mira = (h, v)
        elif self._agachada:
            self.estado, self.mira = Estado.AGACHADA, frente
        else:
            self.estado = Estado.CORRENDO if corpo.vx else Estado.PARADA
            self.mira = (h, -1) if v < 0 else frente
