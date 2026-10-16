"""Ataques dos chefes montados com peças descritas nos dados (D29, D30, D34).

Peças: **rajada** (tiros numa direção), **leque** (vários tiros abrindo a partir da
direção), **mirado** (tiro na direção da Dara no momento do disparo), **chuva** (tiros caindo
do alto em posições sorteadas; podem **explodir** em área ao chegar ao chão), **zona** (área
do chão que machuca enquanto dura), **inimigos** menores (voam até a Dara, machucam no
contato e caem com tiros) e **barra** (um alvo que enche aos poucos: se não for destruído a
tiros antes de encher, o chefe se cura, sem nunca voltar de fase).

Todo ataque passa por três etapas: **aviso** (o jogador vê o que vem: nada machuca ainda),
**ativo** (os tiros saem, a zona machuca) e **espera** (pausa até o próximo). O aviso tem
um mínimo garantido na leitura dos dados (J6, D30). A ordem dos ataques de cada fase é
sorteada com a semente da luta, sem repetir o mesmo ataque duas vezes seguidas (D23).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum

from cupeco.dominio.dados import DadosInvalidos
from cupeco.dominio.fisica import Caixa
from cupeco.dominio.materiais import Material
from cupeco.dominio.projeteis import Dono, Projetil

Ponto = tuple[float, float]

AVISO_MINIMO_NORMAL = 20  # quadros (J6)
AVISO_MINIMO_SIMPLES = 30
COMUM = "comum"  # ataque sem material: só machuca, não pode ser separado
TOLERANCIA_UNITARIA = 1e-3


class TipoAtaque(Enum):
    RAJADA = "rajada"
    LEQUE = "leque"
    MIRADO = "mirado"
    CHUVA = "chuva"
    ZONA = "zona"
    INIMIGOS = "inimigos"
    BARRA = "barra"


TIPOS_COM_TIRO = {TipoAtaque.RAJADA, TipoAtaque.LEQUE, TipoAtaque.MIRADO, TipoAtaque.CHUVA}


@dataclass(frozen=True)
class DadosAtaque:
    nome: str
    tipo: TipoAtaque
    aviso: int  # quadros de aviso antes de qualquer dano
    duracao: int  # quadros da etapa ativa
    espera: int  # quadros de pausa depois
    quantidade: int = 1  # tiros por disparo (rajada, mirado), pontos (chuva) ou inimigos
    intervalo: int = 0  # quadros entre disparos na etapa ativa (0: um disparo só)
    velocidade: float = 0.0
    tamanho: float = 40.0
    dano: int = 1
    materiais: tuple[str, ...] = (COMUM,)
    origem: Ponto | None = None  # de onde sai; sem origem, do centro do chefe
    direcao: Ponto = (-1.0, 0.0)
    espalhamento: tuple[Ponto, ...] = ()  # leque: rotações [cosseno, seno] da direção
    alturas: tuple[float, ...] = ()  # rajada: alturas sorteadas no lugar da origem
    faixa: Ponto = (0.0, 1280.0)  # chuva: de onde a onde caem os tiros
    area: tuple[float, float, float, float] | None = None  # zona e barra: [x, y, larg., alt.]
    vida_inimigo: int = 1
    explode_em: float | None = None  # chuva: altura (y) do chão onde o tiro explode
    explosao: tuple[float, float, int] | None = None  # chuva: [largura, altura, quadros]
    vida_barra: int = 1
    cura: int = 0  # barra: porcentagem da vida máxima que o chefe recupera se ela encher


def _unitario(vetor: Ponto) -> bool:
    return abs(vetor[0] * vetor[0] + vetor[1] * vetor[1] - 1) <= TOLERANCIA_UNITARIA


def validar_ataque(
    ataque: DadosAtaque, onde: str, aviso_minimo: int = AVISO_MINIMO_NORMAL
) -> DadosAtaque:
    """Confere o ataque; `aviso_minimo` é o do modo da luta (J6: 20 no Normal, 30 no Simples)."""
    if ataque.aviso < aviso_minimo:
        raise DadosInvalidos(
            f"{onde}.aviso: todo ataque precisa de pelo menos {aviso_minimo} quadros "
            f"de aviso (J6), veio {ataque.aviso}"
        )
    if ataque.duracao < 1 or ataque.espera < 0 or ataque.intervalo < 0:
        raise DadosInvalidos(f"{onde}: duração, espera e intervalo inválidos")
    if ataque.quantidade < 1 or ataque.dano < 1 or ataque.tamanho <= 0:
        raise DadosInvalidos(f"{onde}: quantidade, dano e tamanho precisam ser positivos")
    validos = {m.value for m in Material} | {COMUM}
    if not ataque.materiais or not set(ataque.materiais) <= validos:
        raise DadosInvalidos(f"{onde}.materiais: use {', '.join(sorted(validos))}")
    tipo = ataque.tipo
    if tipo in TIPOS_COM_TIRO | {TipoAtaque.INIMIGOS} and ataque.velocidade <= 0:
        raise DadosInvalidos(f"{onde}.velocidade: precisa ser positiva")
    if tipo in (TipoAtaque.RAJADA, TipoAtaque.LEQUE) and not _unitario(ataque.direcao):
        raise DadosInvalidos(f"{onde}.direcao: precisa ter tamanho 1")
    if tipo is TipoAtaque.LEQUE and (
        not ataque.espalhamento or not all(_unitario(r) for r in ataque.espalhamento)
    ):
        raise DadosInvalidos(f"{onde}.espalhamento: rotações [cosseno, seno] de tamanho 1")
    if tipo is TipoAtaque.CHUVA and not ataque.faixa[0] < ataque.faixa[1]:
        raise DadosInvalidos(f"{onde}.faixa: o começo precisa vir antes do fim")
    com_area = (TipoAtaque.ZONA, TipoAtaque.BARRA)
    if tipo in com_area and (ataque.area is None or min(ataque.area[2:]) <= 0):
        raise DadosInvalidos(
            f"{onde}.area: a {tipo.value} precisa de uma área [x, y, largura, altura]"
        )
    if tipo is TipoAtaque.INIMIGOS and ataque.vida_inimigo < 1:
        raise DadosInvalidos(f"{onde}.vida_inimigo: precisa ser positiva")
    if (ataque.explode_em is None) != (ataque.explosao is None):
        raise DadosInvalidos(f"{onde}.explosao: use explode_em e explosao juntos")
    if ataque.explosao is not None:
        if tipo is not TipoAtaque.CHUVA:
            raise DadosInvalidos(f"{onde}.explosao: só a chuva explode")
        if min(ataque.explosao) <= 0:
            raise DadosInvalidos(f"{onde}.explosao: largura, altura e quadros positivos")
    if tipo is TipoAtaque.BARRA:
        if ataque.vida_barra < 1:
            raise DadosInvalidos(f"{onde}.vida_barra: precisa ser positiva")
        if not 1 <= ataque.cura <= 100:
            raise DadosInvalidos(f"{onde}.cura: vai de 1 a 100 (% da vida máxima)")
    return ataque


# --- inimigos menores (D34) ----------------------------------------------------------


@dataclass
class Inimigo:
    """Voa até a Dara; machuca no contato e cai com tiros. `x` e `y` são o centro."""

    nome: str
    x: float
    y: float
    tamanho: float
    vida: int
    velocidade: float

    @property
    def caixa(self) -> Caixa:
        metade = self.tamanho / 2
        return Caixa(self.x - metade, self.y - metade, self.tamanho, self.tamanho)

    @property
    def vulneravel(self) -> bool:
        return self.vida > 0

    def levar_dano(self, dano: int) -> list:
        self.vida = max(0, self.vida - dano)
        return []

    def atualizar(self, alvo: Ponto) -> None:
        dx, dy = alvo[0] - self.x, alvo[1] - self.y
        distancia = math.sqrt(dx * dx + dy * dy)
        if distancia <= self.velocidade:
            self.x, self.y = alvo
        else:
            self.x += dx / distancia * self.velocidade
            self.y += dy / distancia * self.velocidade


# --- explosões e barra ---------------------------------------------------------------


@dataclass
class Explosao:
    """Área que machuca por alguns quadros, onde um tiro explosivo chegou ao chão."""

    caixa: Caixa
    restante: int


def explodir(projetil: Projetil) -> Explosao | None:
    """A explosão do projétil, se ele for explosivo e já tiver chegado ao chão."""
    if projetil.explode_em is None or projetil.explosao is None:
        return None
    if projetil.caixa.base < projetil.explode_em:
        return None
    largura, altura, quadros = projetil.explosao
    caixa = Caixa(projetil.x - largura / 2, projetil.explode_em - altura, largura, altura)
    return Explosao(caixa, quadros)


@dataclass
class Barra:
    """Barra que cura o chefe se encher; cai com tiros (que enchem o Medidor)."""

    nome: str
    caixa: Caixa
    vida: int

    @property
    def vulneravel(self) -> bool:
        return self.vida > 0

    def levar_dano(self, dano: int) -> list:
        self.vida = max(0, self.vida - dano)
        return []


# --- roteiro -------------------------------------------------------------------------


class Etapa(Enum):
    AVISO = "aviso"
    ATIVO = "ativo"
    ESPERA = "espera"


@dataclass
class Disparo:
    """O que o roteiro produziu num passo."""

    projeteis: list[Projetil]
    inimigos: list[Inimigo]
    cura: int = 0  # porcentagem da vida máxima: uma barra encheu sem ser destruída


class Roteiro:
    """Escolhe e conduz os ataques de uma fase: aviso → ativo → espera → próximo."""

    def __init__(self, ataques: tuple[DadosAtaque, ...], sorteio: random.Random) -> None:
        self.ataques = ataques
        self._sorteio = sorteio
        self.atual: DadosAtaque | None = None
        self.etapa = Etapa.ESPERA
        self.restante = 0
        self._quadro_ativo = 0
        self._anterior: DadosAtaque | None = None
        self._contador_inimigos = 0
        self._contador_barras = 0
        self._barra: Barra | None = None
        self.pontos_da_chuva: tuple[float, ...] = ()  # sorteados no aviso (o jogador vê onde)

    @property
    def zona_avisada(self) -> Caixa | None:
        """Área da zona durante o aviso (para desenhar o alerta)."""
        if self.atual and self.atual.tipo is TipoAtaque.ZONA and self.etapa is Etapa.AVISO:
            return Caixa(*self.atual.area)
        return None

    @property
    def zona_ativa(self) -> Caixa | None:
        """Área que machuca agora."""
        if self.atual and self.atual.tipo is TipoAtaque.ZONA and self.etapa is Etapa.ATIVO:
            return Caixa(*self.atual.area)
        return None

    @property
    def barra(self) -> Barra | None:
        """A barra em pé agora (destruída, deixa de existir)."""
        return self._barra if self._barra is not None and self._barra.vulneravel else None

    @property
    def barra_avisada(self) -> Caixa | None:
        """Onde a barra vai aparecer, durante o aviso."""
        if self.atual and self.atual.tipo is TipoAtaque.BARRA and self.etapa is Etapa.AVISO:
            return Caixa(*self.atual.area)
        return None

    @property
    def progresso_da_barra(self) -> float:
        """Quanto a barra já encheu, de 0 a 1."""
        if self.barra is None or self.atual is None:
            return 0.0
        return self._quadro_ativo / self.atual.duracao

    def _escolher(self) -> DadosAtaque:
        opcoes = [a for a in self.ataques if a is not self._anterior] or list(self.ataques)
        return self._sorteio.choice(opcoes)

    def atualizar(self, centro_chefe: Ponto, alvo: Ponto) -> tuple[Disparo, list[str]]:
        """Um passo. Devolve o que foi disparado e os nomes das etapas que começaram."""
        disparo = Disparo([], [])
        comecos: list[str] = []
        if not self.ataques:
            return disparo, comecos
        if self.restante > 0:
            self.restante -= 1
        if self.restante == 0:
            terminou = self.atual if self.etapa is Etapa.ATIVO else None
            comecos.append(self._avancar())
            if terminou is not None and terminou.tipo is TipoAtaque.BARRA:
                # A barra encheu: se ninguém a destruiu, o chefe se cura.
                if self.barra is not None:
                    disparo.cura = terminou.cura
                self._barra = None
        if self.etapa is Etapa.ATIVO and self.atual is not None:
            self._agir(self.atual, centro_chefe, alvo, disparo)
            self._quadro_ativo += 1
        return disparo, comecos

    def _avancar(self) -> str:
        if self.etapa is Etapa.ESPERA or self.atual is None:
            self.atual = self._escolher()
            self._anterior = self.atual
            self.etapa, self.restante = Etapa.AVISO, self.atual.aviso
            if self.atual.tipo is TipoAtaque.CHUVA:
                inicio, fim = self.atual.faixa
                self.pontos_da_chuva = tuple(
                    self._sorteio.uniform(inicio, fim) for _ in range(self.atual.quantidade)
                )
        elif self.etapa is Etapa.AVISO:
            self.etapa, self.restante = Etapa.ATIVO, self.atual.duracao
            self._quadro_ativo = 0
        else:
            self.etapa = Etapa.ESPERA
            self.restante = max(1, self.atual.espera)
        return self.etapa.value

    def interromper(self) -> None:
        """Para o ataque atual (troca de fase, derrota): volta à espera."""
        self.atual, self.etapa, self.restante = None, Etapa.ESPERA, 0
        self.pontos_da_chuva = ()
        self._barra = None

    # --- peças ---

    def _deve_disparar(self, ataque: DadosAtaque) -> bool:
        if ataque.intervalo == 0:
            return self._quadro_ativo == 0
        return self._quadro_ativo % ataque.intervalo == 0

    def _material(self, ataque: DadosAtaque) -> Material | None:
        escolha = self._sorteio.choice(ataque.materiais)
        return None if escolha == COMUM else Material(escolha)

    def _tiro(self, ataque: DadosAtaque, x: float, y: float, dx: float, dy: float) -> Projetil:
        return Projetil(
            x=x,
            y=y,
            largura=ataque.tamanho,
            altura=ataque.tamanho,
            vx=dx * ataque.velocidade,
            vy=dy * ataque.velocidade,
            dano=ataque.dano,
            quadros_de_vida=10_000,  # some ao sair da tela
            dono=Dono.INIMIGO,
            material=self._material(ataque),
            explode_em=ataque.explode_em,
            explosao=ataque.explosao,
        )

    def _agir(self, ataque: DadosAtaque, centro: Ponto, alvo: Ponto, disparo: Disparo) -> None:
        if ataque.tipo is TipoAtaque.ZONA or not self._deve_disparar(ataque):
            return
        ox, oy = ataque.origem or centro
        dx, dy = ataque.direcao
        if ataque.tipo is TipoAtaque.RAJADA:
            for _ in range(ataque.quantidade):
                y = self._sorteio.choice(ataque.alturas) if ataque.alturas else oy
                disparo.projeteis.append(self._tiro(ataque, ox, y, dx, dy))
        elif ataque.tipo is TipoAtaque.LEQUE:
            for c, s in ataque.espalhamento:
                rx, ry = dx * c - dy * s, dx * s + dy * c
                disparo.projeteis.append(self._tiro(ataque, ox, oy, rx, ry))
        elif ataque.tipo is TipoAtaque.MIRADO:
            vx, vy = alvo[0] - ox, alvo[1] - oy
            tamanho = math.sqrt(vx * vx + vy * vy)
            if tamanho:
                dx, dy = vx / tamanho, vy / tamanho
            for _ in range(ataque.quantidade):
                disparo.projeteis.append(self._tiro(ataque, ox, oy, dx, dy))
        elif ataque.tipo is TipoAtaque.CHUVA:
            for x in self.pontos_da_chuva:
                disparo.projeteis.append(self._tiro(ataque, x, -ataque.tamanho, 0.0, 1.0))
        elif ataque.tipo is TipoAtaque.BARRA:
            self._contador_barras += 1
            caixa = Caixa(*ataque.area)
            self._barra = Barra(f"barra-{self._contador_barras}", caixa, ataque.vida_barra)
        elif ataque.tipo is TipoAtaque.INIMIGOS:
            for _ in range(ataque.quantidade):
                self._contador_inimigos += 1
                disparo.inimigos.append(
                    Inimigo(
                        nome=f"inimigo-{self._contador_inimigos}",
                        x=ox,
                        y=oy,
                        tamanho=ataque.tamanho,
                        vida=ataque.vida_inimigo,
                        velocidade=ataque.velocidade,
                    )
                )
