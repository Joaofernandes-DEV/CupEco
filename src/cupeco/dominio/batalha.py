"""Uma luta: a Dara, os projéteis e os alvos, avançando em passos fixos (D8, D23, D24).

`Batalha.atualizar(comandos)` avança 1/60 s e devolve os eventos do passo. Todo sorteio
usa `random.Random(semente)`, então a mesma semente com os mesmos comandos dá sempre a
mesma luta: é o que permite gravar um **replay** (semente + lista de comandos) e
reproduzi-lo quadro a quadro.

Na Fase 1 a luta é a da arena de testes: um boneco de treino e um lançador de resíduos.
Os chefes entram na Fase 2.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from enum import Enum
from functools import cache

from cupeco.dominio.comandos import Botao, Comandos
from cupeco.dominio.dados import DadosInvalidos, converter, ler_toml
from cupeco.dominio.fisica import Caixa, Plataforma
from cupeco.dominio.jogador import EventoJogador, Jogador
from cupeco.dominio.materiais import Material
from cupeco.dominio.projeteis import Dono, Projetil

# --- dados da arena ------------------------------------------------------------------


@dataclass(frozen=True)
class DadosPlataforma:
    caixa: tuple[float, float, float, float]
    atravessavel: bool


@dataclass(frozen=True)
class DadosAlvo:
    caixa: tuple[float, float, float, float]


@dataclass(frozen=True)
class DadosLancador:
    x: float
    alturas: tuple[float, ...]
    quadros_entre_lancamentos: int
    velocidade: float
    tamanho: float
    dano: int
    quadros_de_vida: int


@dataclass(frozen=True)
class Arena:
    nome: str
    largura: float
    altura: float
    inicio: tuple[float, float]
    margem: float
    plataformas: tuple[DadosPlataforma, ...]
    alvo: DadosAlvo
    lancador: DadosLancador

    @property
    def plataformas_fisicas(self) -> tuple[Plataforma, ...]:
        return tuple(Plataforma(Caixa(*p.caixa), p.atravessavel) for p in self.plataformas)

    @property
    def area_dos_projeteis(self) -> Caixa:
        m = self.margem
        return Caixa(-m, -m, self.largura + 2 * m, self.altura + 2 * m)


def validar_arena(arena: Arena, onde: str) -> Arena:
    for indice, plataforma in enumerate(arena.plataformas):
        if plataforma.caixa[2] <= 0 or plataforma.caixa[3] <= 0:
            raise DadosInvalidos(f"{onde}.plataformas[{indice}]: largura e altura positivas")
    if not arena.lancador.alturas:
        raise DadosInvalidos(f"{onde}.lancador.alturas: precisa de pelo menos uma altura")
    if arena.lancador.quadros_entre_lancamentos <= 0:
        raise DadosInvalidos(f"{onde}.lancador.quadros_entre_lancamentos: precisa ser positivo")
    return arena


@cache
def carregar_arena(nome: str = "testes") -> Arena:
    bruto = ler_toml("arenas.toml")
    if nome not in bruto:
        raise DadosInvalidos(f"arenas: não existe a arena {nome!r}")
    return validar_arena(converter(bruto[nome], Arena, f"arenas.{nome}"), f"arenas.{nome}")


# --- participantes -------------------------------------------------------------------


@dataclass
class AlvoDeTreino:
    """Boneco de treino: não se mexe, não machuca e soma o dano que recebe."""

    caixa: Caixa
    nome: str = "boneco"
    dano_recebido: int = 0


# Materiais que o lançador sorteia; None é um ataque comum, sem material (só machuca).
SORTEIO_DE_MATERIAIS: tuple[Material | None, ...] = (*Material, None)


class Lancador:
    """Atira um resíduo para a esquerda a cada intervalo, em alturas e materiais sorteados."""

    def __init__(self, dados: DadosLancador, sorteio: random.Random) -> None:
        self.dados = dados
        self._sorteio = sorteio
        self._espera = dados.quadros_entre_lancamentos

    def atualizar(self) -> Projetil | None:
        self._espera -= 1
        if self._espera > 0:
            return None
        self._espera = self.dados.quadros_entre_lancamentos
        d = self.dados
        return Projetil(
            x=d.x,
            y=self._sorteio.choice(d.alturas),
            largura=d.tamanho,
            altura=d.tamanho,
            vx=-d.velocidade,
            vy=0.0,
            dano=d.dano,
            quadros_de_vida=d.quadros_de_vida,
            dono=Dono.INIMIGO,
            material=self._sorteio.choice(SORTEIO_DE_MATERIAIS),
        )


# --- a luta --------------------------------------------------------------------------


class EventoBatalha(Enum):
    ACERTOU_ALVO = "acertou_alvo"
    SUPER_ACERTOU = "super_acertou"
    RESIDUO_LANCADO = "residuo_lancado"


Evento = EventoJogador | EventoBatalha


@dataclass
class Batalha:
    """Uma luta na arena de testes. Use `atualizar` uma vez por passo de 1/60 s."""

    semente: int
    arena: Arena = field(default_factory=carregar_arena)

    def __post_init__(self) -> None:
        self.sorteio = random.Random(self.semente)
        self.plataformas = self.arena.plataformas_fisicas
        self.jogador = Jogador(*self.arena.inicio)
        self.alvo = AlvoDeTreino(Caixa(*self.arena.alvo.caixa))
        self.lancador = Lancador(self.arena.lancador, self.sorteio)
        self.projeteis: list[Projetil] = []
        self.quadro = 0
        self.gravacao: list[Comandos] = []

    def atualizar(self, comandos: Comandos) -> list[Evento]:
        comandos = frozenset(comandos)
        self.gravacao.append(comandos)
        jogador = self.jogador
        eventos: list[Evento] = list(jogador.atualizar(comandos, self.plataformas))
        self.projeteis.extend(jogador.novos_projeteis)

        if EventoJogador.SUPER in eventos:
            self.alvo.dano_recebido += jogador.regras.dano_super
            eventos.append(EventoBatalha.SUPER_ACERTOU)

        lancado = self.lancador.atualizar()
        if lancado is not None:
            self.projeteis.append(lancado)
            eventos.append(EventoBatalha.RESIDUO_LANCADO)

        for projetil in self.projeteis:
            projetil.atualizar()
        eventos.extend(self._colisoes())
        area = self.arena.area_dos_projeteis
        self.projeteis = [p for p in self.projeteis if p.vivo and not p.fora_da_area(area)]
        self.quadro += 1
        return eventos

    def _colisoes(self) -> list[Evento]:
        eventos: list[Evento] = []
        jogador = self.jogador
        restantes = []
        alvo = self.alvo
        for projetil in self.projeteis:
            remover = False
            if projetil.dono is Dono.JOGADOR:
                novo_acerto = alvo.nome not in projetil.alvos_atingidos
                if novo_acerto and projetil.caixa.sobrepoe(alvo.caixa):
                    alvo.dano_recebido += projetil.dano
                    jogador.acertou(projetil)
                    eventos.append(EventoBatalha.ACERTOU_ALVO)
                    projetil.alvos_atingidos.add(alvo.nome)
                    remover = not projetil.perfura
            elif projetil.caixa.sobrepoe(jogador.corpo.caixa):
                toque = jogador.tocar(projetil)
                eventos.extend(toque.eventos)
                remover = toque.remover_projetil
            if not remover:
                restantes.append(projetil)
        self.projeteis = restantes
        return eventos

    def retrato(self) -> tuple:
        """O estado que importa da luta, para comparar duas execuções."""
        corpo = self.jogador.corpo
        return (
            self.quadro,
            corpo.x,
            corpo.y,
            corpo.vx,
            corpo.vy,
            self.jogador.estado,
            self.jogador.vida,
            self.jogador.medidor.pontos,
            self.alvo.dano_recebido,
            tuple((p.x, p.y, p.dono, p.material) for p in self.projeteis),
        )


# --- replay --------------------------------------------------------------------------

VERSAO_REPLAY = 1


@dataclass(frozen=True)
class Replay:
    """Uma luta gravada: a semente e os botões segurados em cada passo."""

    semente: int
    comandos: tuple[Comandos, ...]
    arena: str = "testes"

    @classmethod
    def da_batalha(cls, batalha: Batalha, arena: str = "testes") -> Replay:
        return cls(batalha.semente, tuple(batalha.gravacao), arena)

    def para_json(self) -> str:
        return json.dumps(
            {
                "versao": VERSAO_REPLAY,
                "arena": self.arena,
                "semente": self.semente,
                "comandos": [sorted(b.value for b in passo) for passo in self.comandos],
            },
            ensure_ascii=False,
        )

    @classmethod
    def de_json(cls, texto: str) -> Replay:
        dados = json.loads(texto)
        if dados.get("versao") != VERSAO_REPLAY:
            raise DadosInvalidos(f"replay: versão {dados.get('versao')!r} não suportada")
        try:
            comandos = tuple(frozenset(Botao(b) for b in passo) for passo in dados["comandos"])
        except ValueError as erro:
            raise DadosInvalidos(f"replay: botão desconhecido ({erro})") from erro
        return cls(int(dados["semente"]), comandos, str(dados["arena"]))

    def reproduzir(self) -> tuple[Batalha, list[list[Evento]]]:
        """Roda a luta inteira de novo; devolve a batalha final e os eventos de cada passo."""
        batalha = Batalha(self.semente, carregar_arena(self.arena))
        eventos = [batalha.atualizar(passo) for passo in self.comandos]
        return batalha, eventos
