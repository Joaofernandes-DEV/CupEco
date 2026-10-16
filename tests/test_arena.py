"""Arena de testes e entrada, sem janela (driver dummy do SDL)."""

import pygame
import pytest

from cupeco.__main__ import main
from cupeco.dominio.comandos import NENHUM, Botao
from cupeco.dominio.jogador import EventoJogador
from cupeco.dominio.materiais import Material
from cupeco.estados.arena import OPCOES_PAUSA, EstadoArena
from cupeco.estados.titulo import EstadoTitulo
from cupeco.ui.entrada import comandos_do_controle, comandos_do_teclado, e_pausa


class TeclasFalsas(dict):
    """Imita `pygame.key.get_pressed()`: tecla não listada está solta."""

    def __missing__(self, tecla):
        return False


class ControleFalso:
    def __init__(self, botoes=(), eixos=None):
        self.botoes = set(botoes)
        self.eixos = eixos or {}

    def get_button(self, botao):
        return botao in self.botoes

    def get_axis(self, eixo):
        return self.eixos.get(eixo, 0)


def tecla(codigo):
    return pygame.Event(pygame.KEYDOWN, key=codigo)


def arena(jogo, comandos=NENHUM):
    return EstadoArena(jogo, semente=1, leitor=lambda: comandos)


# --- entrada (D24, I8) ---------------------------------------------------------------


def test_teclado_vira_botoes():
    teclas = TeclasFalsas({pygame.K_z: True, pygame.K_RIGHT: True, pygame.K_RSHIFT: True})
    assert comandos_do_teclado(teclas) == {Botao.PULO, Botao.DIREITA, Botao.TRAVAR}
    assert comandos_do_teclado(TeclasFalsas()) == NENHUM


def test_controle_vira_botoes_com_analogico_e_gatilho():
    controle = ControleFalso(
        botoes={pygame.CONTROLLER_BUTTON_A, pygame.CONTROLLER_BUTTON_RIGHTSHOULDER},
        eixos={
            pygame.CONTROLLER_AXIS_LEFTX: -30000,
            pygame.CONTROLLER_AXIS_LEFTY: 20000,
            pygame.CONTROLLER_AXIS_TRIGGERRIGHT: 32767,
        },
    )
    assert comandos_do_controle(controle) == {
        Botao.PULO,
        Botao.DASH,
        Botao.ESQUERDA,
        Botao.BAIXO,
        Botao.TIRO,
    }


def test_analogico_pouco_inclinado_nao_conta():
    controle = ControleFalso(eixos={pygame.CONTROLLER_AXIS_LEFTX: 8000})
    assert comandos_do_controle(controle) == NENHUM


def test_esc_e_start_pausam():
    assert e_pausa(tecla(pygame.K_ESCAPE))
    assert e_pausa(pygame.Event(pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_START))
    assert not e_pausa(tecla(pygame.K_z))


# --- título e arena ------------------------------------------------------------------


def test_enter_no_titulo_abre_a_arena(jogo):
    jogo.trocar_estado(EstadoTitulo(jogo))
    jogo.estado.tratar_evento(tecla(pygame.K_RETURN))
    assert isinstance(jogo.estado, EstadoArena)


def test_atirar_na_arena_acerta_o_boneco(jogo):
    estado = arena(jogo, frozenset({Botao.TIRO}))
    for _ in range(120):
        estado.atualizar()
    assert estado.batalha.alvo.dano_recebido > 0
    estado.desenhar(jogo.tela)


def test_pausa_congela_a_luta(jogo):
    estado = arena(jogo)
    estado.atualizar()
    estado.tratar_evento(tecla(pygame.K_ESCAPE))
    assert estado.pausa_aberta
    quadro = estado.batalha.quadro
    for _ in range(30):
        estado.atualizar()
    assert estado.batalha.quadro == quadro
    estado.desenhar(jogo.tela)
    estado.tratar_evento(tecla(pygame.K_RETURN))  # "Continuar"
    assert not estado.pausa_aberta


def test_pausa_reiniciar_comeca_a_luta_de_novo(jogo):
    estado = arena(jogo, frozenset({Botao.TIRO}))
    for _ in range(60):
        estado.atualizar()
    estado.tratar_evento(tecla(pygame.K_ESCAPE))
    estado.tratar_evento(tecla(pygame.K_DOWN))
    assert OPCOES_PAUSA[estado.opcao] == "Reiniciar"
    estado.tratar_evento(tecla(pygame.K_RETURN))
    assert estado.batalha.quadro == 0 and not estado.pausa_aberta


def test_pausa_sair_volta_ao_titulo(jogo):
    estado = arena(jogo)
    jogo.trocar_estado(estado)
    estado.tratar_evento(tecla(pygame.K_ESCAPE))
    estado.tratar_evento(tecla(pygame.K_UP))  # de "Continuar" volta para a última opção
    assert OPCOES_PAUSA[estado.opcao] == "Sair para o título"
    estado.tratar_evento(tecla(pygame.K_RETURN))
    assert isinstance(jogo.estado, EstadoTitulo)


def test_f1_mostra_as_caixas(jogo):
    estado = arena(jogo)
    estado.tratar_evento(tecla(pygame.K_F1))
    assert estado.mostrar_caixas
    estado.atualizar()
    estado.desenhar(jogo.tela)
    estado.tratar_evento(tecla(pygame.K_F1))
    assert not estado.mostrar_caixas


def test_derrotada_tenta_de_novo_com_enter(jogo):
    estado = arena(jogo)
    estado.atualizar()
    estado.batalha.jogador.vida = 1
    estado.batalha.jogador.tocar_perigo()
    assert estado.batalha.jogador.derrotada
    estado.desenhar(jogo.tela)
    estado.tratar_evento(tecla(pygame.K_RETURN))
    assert not estado.batalha.jogador.derrotada and estado.batalha.quadro == 0


@pytest.mark.parametrize(
    ("material", "evento", "trecho"),
    [
        (Material.PLASTICO, EventoJogador.TRIAGEM_CERTA, "Plástico na lixeira vermelha: +1 fardo"),
        (Material.VIDRO, EventoJogador.TRIAGEM_OUTRA_COR, "Vidro é da lixeira verde"),
        (Material.PERIGOSO, EventoJogador.TRIAGEM_PROIBIDA, "coleta especial"),
        (Material.REJEITO, EventoJogador.TRIAGEM_PROIBIDA, "vai para o aterro"),
    ],
)
def test_aviso_explica_a_triagem(jogo, material, evento, trecho):
    estado = arena(jogo)
    estado.batalha.jogador.ultimo_residuo = material
    estado._avisar([evento])
    assert estado.aviso is not None and trecho in estado.aviso[0]
    estado.desenhar(jogo.tela)


def test_aviso_some_depois_de_um_tempo(jogo):
    estado = arena(jogo)
    estado.batalha.jogador.ultimo_residuo = Material.PAPEL
    estado._avisar([EventoJogador.TRIAGEM_CERTA])
    for _ in range(200):
        estado.atualizar()
    assert estado.aviso is None


def test_opcao_arena_abre_direto_na_arena():
    main(["--arena", "--semente", "3", "--fechar-em", "0.3"])
    assert not pygame.get_init()
