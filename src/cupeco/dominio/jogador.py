"""A Dara: movimento, tiro, Triagem, Medidor, dano e vida (J1 a J5, D12, D14).

Tudo avança em passos fixos (D8) a partir dos botões segurados (D24); os valores vêm de
`conteudo/jogador.toml`, `conteudo/armas.toml` e `conteudo/triagem.toml` (D26).

Quem confere as colisões é a batalha (PR 7): ela chama `tocar` quando um projétil inimigo
encosta na Dara, `tocar_perigo` para contato com o corpo de um inimigo e `acertou` quando
um tiro da Dara acerta um alvo.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields
from enum import Enum
from functools import cache

from cupeco.dominio.armas import Arsenal, boca_do_canhao, disparar_ex
from cupeco.dominio.comandos import Botao, Comandos, Controle, Direcao
from cupeco.dominio.dados import DadosInvalidos, converter, ler_toml
from cupeco.dominio.fisica import Corpo, Plataforma, apoios, mover
from cupeco.dominio.materiais import Material
from cupeco.dominio.medidor import Medidor
from cupeco.dominio.projeteis import Dono, Projetil
from cupeco.dominio.triagem import (
    RegrasTriagem,
    ResultadoTriagem,
    carregar_regras_triagem,
    resolver,
)

MUITO_TEMPO = 1_000_000  # "faz muito tempo" para os contadores de quadros


class Estado(Enum):
    PARADA = "parada"
    CORRENDO = "correndo"
    AGACHADA = "agachada"
    TRAVADA = "travada"
    NO_AR = "no_ar"
    DASH = "dash"
    TRIAGEM = "triagem"
    DANO = "dano"
    SUPER = "super"
    DERROTADA = "derrotada"


class EventoJogador(Enum):
    """Acontecimentos de um passo, para a interface tocar sons e animações."""

    PULOU = "pulou"
    POUSOU = "pousou"
    DASH = "dash"
    DESCEU = "desceu"
    TIROU = "tirou"
    TROCOU_ARMA = "trocou_arma"
    TENTOU_TRIAGEM = "tentou_triagem"
    TRIAGEM_CERTA = "triagem_certa"
    TRIAGEM_OUTRA_COR = "triagem_outra_cor"
    TRIAGEM_PROIBIDA = "triagem_proibida"
    LEVOU_DANO = "levou_dano"
    DERROTADA = "derrotada"
    EX = "ex"
    SUPER = "super"


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
    distancia_boca: float
    vida_maxima: int
    quadros_atordoada: int
    quadros_invencivel: int
    velocidade_empurrao: float
    quadros_janela_triagem: int
    velocidade_quique: float


def validar_parametros(p: ParametrosJogador) -> ParametrosJogador:
    for campo in fields(p):
        valor = getattr(p, campo.name)
        if valor < 0 or (valor == 0 and campo.name != "quadros_espera_dash"):
            raise DadosInvalidos(f"jogador.{campo.name}: precisa ser positivo, veio {valor}")
    if p.altura_agachada >= p.altura:
        raise DadosInvalidos("jogador.altura_agachada: precisa ser menor que a altura")
    if p.corte_pulo > 1:
        raise DadosInvalidos("jogador.corte_pulo: vai de 0 a 1")
    if p.quadros_invencivel <= p.quadros_atordoada:
        raise DadosInvalidos("jogador.quadros_invencivel: precisa durar mais que o atordoamento")
    return p


@cache
def carregar_parametros_jogador() -> ParametrosJogador:
    return validar_parametros(converter(ler_toml("jogador.toml"), ParametrosJogador, "jogador"))


@dataclass
class Estatisticas:
    """Contagens da luta, para a nota (J14) e para a tela de resultado."""

    triagens_certas: int = 0
    triagens_outra_cor: int = 0
    triagens_proibidas: int = 0
    danos_recebidos: int = 0
    exs: int = 0
    supers: int = 0


@dataclass(frozen=True)
class Toque:
    """Resultado de um projétil inimigo encostar na Dara."""

    remover_projetil: bool
    eventos: tuple[EventoJogador, ...] = ()


class Jogador:
    """A Dara. `x` é a borda esquerda da caixa e `base` a altura dos pés."""

    def __init__(
        self,
        x: float,
        base: float,
        parametros: ParametrosJogador | None = None,
        arsenal: Arsenal | None = None,
        regras: RegrasTriagem | None = None,
    ):
        self.p = parametros or carregar_parametros_jogador()
        self.regras = regras or carregar_regras_triagem()
        self.arsenal = arsenal or Arsenal.padrao()
        self.medidor = Medidor()
        self.estatisticas = Estatisticas()
        self.vida = self.p.vida_maxima
        self.novos_projeteis: list[Projetil] = []  # disparados no último passo
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
        self._triagem_restante = 0
        self._triagem_disponivel = True
        self._atordoada = 0
        self._invencivel = 0
        self._super_restante = 0
        # Material do último resíduo que encostou na Dara (para a interface explicar a Triagem).
        self.ultimo_residuo: Material | None = None

    # --- consultas ------------------------------------------------------------------

    @property
    def derrotada(self) -> bool:
        return self.vida == 0

    @property
    def invencivel(self) -> bool:
        return self.derrotada or self._invencivel > 0 or self._super_restante > 0

    @property
    def em_triagem(self) -> bool:
        return self._triagem_restante > 0

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
        corpo, controle = self.corpo, self.controle
        plataformas = list(plataformas)
        controle.atualizar(segurados)
        self.novos_projeteis = []
        eventos: list[EventoJogador] = []
        estava_no_chao = corpo.no_chao
        self._contar_tempos()

        if self.derrotada or self._atordoada > 0:
            # Sem controle: só a física, mantendo o empurrão do dano.
            mover(corpo, plataformas, self.p.gravidade, self.p.queda_maxima)
            self._depois_de_mover(estava_no_chao, eventos)
            self.estado = Estado.DERROTADA if self.derrotada else Estado.DANO
            return eventos
        if self._super_restante > 0:
            # Soltando a Prensa: parada no lugar, invencível.
            corpo.vx = corpo.vy = 0.0
            self.estado = Estado.SUPER
            return eventos

        if controle.apertou(Botao.PULO):
            self._pulo_guardado = self.p.quadros_pulo_guardado
        elif self._pulo_guardado > 0:
            self._pulo_guardado -= 1
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

        self._depois_de_mover(estava_no_chao, eventos)
        self._atualizar_estado_e_mira(travada, em_dash)
        eventos.extend(self._atirar(em_dash))
        return eventos

    def _contar_tempos(self) -> None:
        for nome in (
            "_espera_dash",
            "_descer",
            "_triagem_restante",
            "_atordoada",
            "_invencivel",
            "_super_restante",
        ):
            valor = getattr(self, nome)
            if valor > 0:
                setattr(self, nome, valor - 1)

    def _depois_de_mover(self, estava_no_chao: bool, eventos: list[EventoJogador]) -> None:
        if self.corpo.no_chao:
            self._desde_o_chao = 0
            self._dash_aereo = True
            self._triagem_disponivel = True
            self._triagem_restante = 0
            if not estava_no_chao:
                eventos.append(EventoJogador.POUSOU)
        elif self._desde_o_chao < MUITO_TEMPO:
            self._desde_o_chao += 1

    def _atirar(self, em_dash: bool) -> list[EventoJogador]:
        """Troca de arma, tiro contínuo, EX e Super; nada disso durante o dash."""
        eventos = []
        controle = self.controle
        if em_dash:
            self.arsenal.atualizar(False, (0.0, 0.0), self.mira)
            return eventos
        if controle.apertou(Botao.TROCAR):
            self.arsenal.trocar()
            eventos.append(EventoJogador.TROCOU_ARMA)
        origem = boca_do_canhao(self.corpo.caixa, self.mira, self.p.distancia_boca)
        if controle.apertou(Botao.EX):
            # Com o Medidor cheio, o botão do EX solta o Super (a Prensa).
            if self.medidor.gastar_super():
                self._super_restante = self.regras.quadros_super
                self.estatisticas.supers += 1
                eventos.append(EventoJogador.SUPER)
                return eventos
            if self.medidor.gastar_ex():
                self.novos_projeteis.append(disparar_ex(self.arsenal.ativa, origem, self.mira))
                self.estatisticas.exs += 1
                eventos.append(EventoJogador.EX)
        disparos = self.arsenal.atualizar(controle.segurando(Botao.TIRO), origem, self.mira)
        if disparos:
            self.novos_projeteis.extend(disparos)
            eventos.append(EventoJogador.TIROU)
        return eventos

    def _iniciar_dash(self) -> None:
        self._dash_restante = self.p.quadros_dash
        self._dash_direcao = self.controle.horizontal or self.virada
        self.virada = self._dash_direcao
        if not self.corpo.no_chao:
            self._dash_aereo = False
        self._pulo_cortavel = False
        self._triagem_restante = 0
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
        elif not corpo.no_chao and controle.apertou(Botao.PULO) and self._triagem_disponivel:
            # Pulo apertado no ar (fora da tolerância da beirada): tentativa de Triagem. O
            # aperto continua guardado: se a Dara pousar logo em seguida, ela pula.
            self._triagem_restante = p.quadros_janela_triagem
            self._triagem_disponivel = False
            eventos.append(EventoJogador.TENTOU_TRIAGEM)

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
            self.estado = Estado.TRIAGEM if self.em_triagem else Estado.NO_AR
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

    # --- colisões (chamadas pela batalha) ------------------------------------------

    def tocar(self, projetil: Projetil) -> Toque:
        """Um projétil inimigo encostou na Dara: Triagem (se a janela estiver aberta) ou dano."""
        if projetil.dono is not Dono.INIMIGO:
            raise ValueError("só projéteis inimigos tocam a Dara")
        if self.invencivel:
            return Toque(remover_projetil=False)
        self.ultimo_residuo = projetil.material
        if self.em_triagem and projetil.material is not None:
            resolucao = resolver(projetil.material, self.arsenal.ativa.material, self.regras)
            if resolucao.separou:
                return self._separar(resolucao.resultado, resolucao.pontos)
            self.estatisticas.triagens_proibidas += 1
            return Toque(False, (EventoJogador.TRIAGEM_PROIBIDA, *self._levar_dano()))
        return Toque(False, self._levar_dano())

    def tocar_perigo(self) -> tuple[EventoJogador, ...]:
        """Contato com algo que machuca e não é projétil (o corpo de um chefe, por exemplo)."""
        if self.invencivel:
            return ()
        return self._levar_dano()

    def acertou(self, projetil: Projetil) -> None:
        """Um tiro da Dara acertou um alvo: o dano dos tiros normais enche o Medidor (J4)."""
        if not projetil.ex:
            self.medidor.ganhar(projetil.dano * self.regras.pontos_por_dano)

    def _separar(self, resultado: ResultadoTriagem, pontos: int) -> Toque:
        """Triagem bem-sucedida: pontos no Medidor e um quique para encadear."""
        self.medidor.ganhar(pontos)
        self.corpo.vy = -self.p.velocidade_quique
        self._pulo_cortavel = False
        self._triagem_restante = 0
        self._triagem_disponivel = True
        self._dash_aereo = True
        if resultado is ResultadoTriagem.CERTA:
            self.estatisticas.triagens_certas += 1
            return Toque(True, (EventoJogador.TRIAGEM_CERTA,))
        self.estatisticas.triagens_outra_cor += 1
        return Toque(True, (EventoJogador.TRIAGEM_OUTRA_COR,))

    def _levar_dano(self) -> tuple[EventoJogador, ...]:
        self.vida -= 1
        self.estatisticas.danos_recebidos += 1
        self._dash_restante = 0
        self._triagem_restante = 0
        self._pulo_cortavel = False
        self._ficar_em_pe()
        if self.derrotada:
            self.corpo.vx = 0.0
            self.estado = Estado.DERROTADA
            return (EventoJogador.LEVOU_DANO, EventoJogador.DERROTADA)
        self._atordoada = self.p.quadros_atordoada
        self._invencivel = self.p.quadros_invencivel
        self.corpo.vx = -self.virada * self.p.velocidade_empurrao / 2
        self.corpo.vy = -self.p.velocidade_empurrao
        self.estado = Estado.DANO
        return (EventoJogador.LEVOU_DANO,)
