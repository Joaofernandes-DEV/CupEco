"""Uma luta: a Dara, os projéteis e os alvos, avançando em passos fixos (D8, D23, D24).

`Batalha.atualizar(comandos)` avança 1/60 s e devolve os eventos do passo. Todo sorteio
usa `random.Random(semente)`, então a mesma semente com os mesmos comandos dá sempre a
mesma luta: é o que permite gravar um **replay** (semente + lista de comandos) e
reproduzi-lo quadro a quadro.

A arena de testes tem um boneco de treino e um lançador de resíduos; uma luta de verdade
tem um chefe (D28). Os tiros da Dara acertam qualquer alvo (boneco ou chefe); o chefe
também machuca por contato, e os tiros explosivos viram explosões ao chegar ao chão. A
barra de um chefe (a "Atualização Obrigatória" do Dom) também é alvo dos tiros. O modo da
luta (Normal ou Simples, D31) é aplicado ao chefe ao começar; a arena de testes não muda
com o modo.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from enum import Enum
from functools import cache

from cupeco.dominio.ataques import Explosao, Inimigo, explodir
from cupeco.dominio.chefe import Chefe, DadosChefe, EventoChefe, carregar_chefe
from cupeco.dominio.comandos import Botao, Comandos
from cupeco.dominio.dados import DadosInvalidos, converter, ler_toml
from cupeco.dominio.fisica import Caixa, Plataforma
from cupeco.dominio.jogador import EventoJogador, Jogador
from cupeco.dominio.materiais import Material
from cupeco.dominio.modos import Modo, aplicar_modo
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
    # Só a arena de testes tem boneco e lançador.
    alvo: DadosAlvo | None = None
    lancador: DadosLancador | None = None

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
    if arena.lancador is not None:
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

    @property
    def vulneravel(self) -> bool:
        return True

    def levar_dano(self, dano: int) -> list[EventoChefe]:
        self.dano_recebido += dano
        return []


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
    INIMIGO_DESTRUIDO = "inimigo_destruido"
    EXPLODIU = "explodiu"  # um tiro explosivo chegou ao chão
    BARRA_DESTRUIDA = "barra_destruida"


class Resultado(Enum):
    VITORIA = "vitoria"
    DERROTA = "derrota"


Evento = EventoJogador | EventoBatalha | EventoChefe


@dataclass
class Batalha:
    """Uma luta. Use `atualizar` uma vez por passo de 1/60 s."""

    semente: int
    arena: Arena = field(default_factory=carregar_arena)
    dados_chefe: DadosChefe | None = None  # como está nos dados, antes do modo
    modo: Modo = Modo.NORMAL

    def __post_init__(self) -> None:
        self.sorteio = random.Random(self.semente)
        self.plataformas = self.arena.plataformas_fisicas
        self.jogador = Jogador(*self.arena.inicio)
        dados_alvo, dados_lancador = self.arena.alvo, self.arena.lancador
        self.alvo = AlvoDeTreino(Caixa(*dados_alvo.caixa)) if dados_alvo else None
        self.lancador = Lancador(dados_lancador, self.sorteio) if dados_lancador else None
        self.chefe = (
            Chefe(aplicar_modo(self.dados_chefe, self.modo), self.sorteio)
            if self.dados_chefe
            else None
        )
        self.inimigos: list[Inimigo] = []
        self.explosoes: list[Explosao] = []
        self.alvos: list[AlvoDeTreino | Chefe] = [a for a in (self.alvo, self.chefe) if a]
        self.projeteis: list[Projetil] = []
        self.quadro = 0
        self.gravacao: list[Comandos] = []

    @property
    def resultado(self) -> Resultado | None:
        if self.chefe is not None and self.chefe.derrotado:
            return Resultado.VITORIA
        if self.jogador.derrotada:
            return Resultado.DERROTA
        return None

    def _ferir(self, alvo: AlvoDeTreino | Chefe, dano: int) -> list[Evento]:
        """Aplica dano num alvo vulnerável e devolve os eventos (vazio se não acertou)."""
        if not alvo.vulneravel:
            return []
        return [EventoBatalha.ACERTOU_ALVO, *alvo.levar_dano(dano)]

    def atualizar(self, comandos: Comandos) -> list[Evento]:
        comandos = frozenset(comandos)
        self.gravacao.append(comandos)
        jogador = self.jogador
        eventos: list[Evento] = list(jogador.atualizar(comandos, self.plataformas))
        self.projeteis.extend(jogador.novos_projeteis)

        if EventoJogador.SUPER in eventos:
            for alvo in self.alvos:
                acerto = self._ferir(alvo, jogador.regras.dano_super)
                if acerto:
                    eventos.append(EventoBatalha.SUPER_ACERTOU)
                    eventos.extend(acerto[1:])

        centro_dara = jogador.corpo.caixa.centro
        if self.chefe is not None:
            chefe = self.chefe
            eventos.extend(chefe.atualizar(centro_dara))
            self.projeteis.extend(chefe.novos_projeteis)
            self.inimigos.extend(chefe.novos_inimigos)
            caixa_dara = jogador.corpo.caixa
            contato = chefe.dados.dano_por_contato and not chefe.derrotado
            if contato and chefe.caixa.sobrepoe(caixa_dara):
                eventos.extend(jogador.tocar_perigo())
            zona = chefe.zona_ativa
            if zona is not None and zona.sobrepoe(caixa_dara):
                eventos.extend(jogador.tocar_perigo())

        restantes = []
        for inimigo in self.inimigos:
            inimigo.atualizar(centro_dara)
            if inimigo.caixa.sobrepoe(jogador.corpo.caixa) and not jogador.invencivel:
                eventos.extend(jogador.tocar_perigo())
                eventos.append(EventoBatalha.INIMIGO_DESTRUIDO)
            else:
                restantes.append(inimigo)
        self.inimigos = restantes

        if self.lancador is not None:
            lancado = self.lancador.atualizar()
            if lancado is not None:
                self.projeteis.append(lancado)
                eventos.append(EventoBatalha.RESIDUO_LANCADO)

        for projetil in self.projeteis:
            projetil.atualizar()
        eventos.extend(self._explosoes())
        eventos.extend(self._colisoes())
        area = self.arena.area_dos_projeteis
        self.projeteis = [p for p in self.projeteis if p.vivo and not p.fora_da_area(area)]
        self.quadro += 1
        return eventos

    def _explosoes(self) -> list[Evento]:
        """Tiros explosivos que chegaram ao chão viram explosões; as explosões machucam."""
        eventos: list[Evento] = []
        restantes = []
        for projetil in self.projeteis:
            explosao = explodir(projetil)
            if explosao is None:
                restantes.append(projetil)
            else:
                self.explosoes.append(explosao)
                eventos.append(EventoBatalha.EXPLODIU)
        self.projeteis = restantes
        ativas = []
        for explosao in self.explosoes:
            if explosao.caixa.sobrepoe(self.jogador.corpo.caixa):
                eventos.extend(self.jogador.tocar_perigo())
            explosao.restante -= 1
            if explosao.restante > 0:
                ativas.append(explosao)
        self.explosoes = ativas
        return eventos

    def _colisoes(self) -> list[Evento]:
        eventos: list[Evento] = []
        jogador = self.jogador
        barra = self.chefe.barra if self.chefe is not None else None
        restantes = []
        for projetil in self.projeteis:
            remover = False
            if projetil.dono is Dono.JOGADOR:
                for alvo in [*self.alvos, *self.inimigos, *([barra] if barra else [])]:
                    if alvo.nome in projetil.alvos_atingidos:
                        continue
                    if not projetil.caixa.sobrepoe(alvo.caixa):
                        continue
                    # Alvo invulnerável (chefe em transição) absorve o tiro sem levar dano.
                    acerto = self._ferir(alvo, projetil.dano)
                    if acerto:
                        jogador.acertou(projetil)
                        eventos.extend(acerto)
                    projetil.alvos_atingidos.add(alvo.nome)
                    if not projetil.perfura:
                        remover = True
                        break
            elif projetil.caixa.sobrepoe(jogador.corpo.caixa):
                toque = jogador.tocar(projetil)
                eventos.extend(toque.eventos)
                remover = toque.remover_projetil
            if not remover:
                restantes.append(projetil)
        self.projeteis = restantes
        vivos = [inimigo for inimigo in self.inimigos if inimigo.vida > 0]
        eventos.extend([EventoBatalha.INIMIGO_DESTRUIDO] * (len(self.inimigos) - len(vivos)))
        self.inimigos = vivos
        if barra is not None and not barra.vulneravel:
            eventos.append(EventoBatalha.BARRA_DESTRUIDA)
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
            self.alvo.dano_recebido if self.alvo else None,
            (self.chefe.vida, self.chefe.fase, self.chefe.x, self.chefe.y) if self.chefe else None,
            tuple((i.nome, i.x, i.y, i.vida) for i in self.inimigos),
            tuple((p.x, p.y, p.dono, p.material) for p in self.projeteis),
            tuple((e.caixa, e.restante) for e in self.explosoes),
            (self.chefe.barra.nome, self.chefe.barra.vida)
            if self.chefe and self.chefe.barra
            else None,
        )


# --- replay --------------------------------------------------------------------------

VERSAO_REPLAY = 1


@dataclass(frozen=True)
class Replay:
    """Uma luta gravada: a semente, o modo e os botões segurados em cada passo."""

    semente: int
    comandos: tuple[Comandos, ...]
    arena: str = "testes"
    chefe: str | None = None  # nome do arquivo em conteudo/chefes/, sem o .toml
    modo: Modo = Modo.NORMAL

    @classmethod
    def da_batalha(
        cls, batalha: Batalha, arena: str = "testes", chefe: str | None = None
    ) -> Replay:
        return cls(batalha.semente, tuple(batalha.gravacao), arena, chefe, batalha.modo)

    def para_json(self) -> str:
        return json.dumps(
            {
                "versao": VERSAO_REPLAY,
                "arena": self.arena,
                "chefe": self.chefe,
                "modo": self.modo.value,
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
        chefe = dados.get("chefe")
        # Replays gravados antes dos modos não têm o campo: eram todos Normal.
        try:
            modo = Modo(dados.get("modo", Modo.NORMAL.value))
        except ValueError as erro:
            raise DadosInvalidos(f"replay: modo desconhecido ({erro})") from erro
        return cls(int(dados["semente"]), comandos, str(dados["arena"]), chefe, modo)

    def reproduzir(self) -> tuple[Batalha, list[list[Evento]]]:
        """Roda a luta inteira de novo; devolve a batalha final e os eventos de cada passo."""
        dados_chefe = carregar_chefe(self.chefe) if self.chefe else None
        batalha = Batalha(self.semente, carregar_arena(self.arena), dados_chefe, self.modo)
        eventos = [batalha.atualizar(passo) for passo in self.comandos]
        return batalha, eventos
