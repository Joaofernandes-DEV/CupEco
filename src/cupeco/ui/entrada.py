"""Entrada: teclado e controle viram o conjunto de botões segurados (D24, I8).

Teclado: setas movem, Z pula/Triagem, X atira, C dash, V EX/Super, Shift trava,
Tab troca de arma. Controle (padrão Xbox, via SDL GameController): analógico esquerdo ou
direcional, A pula, X atira, B EX/Super, Y troca, RB dash, LB trava; o gatilho direito
também atira. Esc e Start pausam (tratados como eventos pela tela).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

import pygame
from pygame._sdl2 import controller as sdl_controle

from cupeco.dominio.comandos import Botao, Comandos

TECLAS: Mapping[Botao, tuple[int, ...]] = {
    Botao.ESQUERDA: (pygame.K_LEFT,),
    Botao.DIREITA: (pygame.K_RIGHT,),
    Botao.CIMA: (pygame.K_UP,),
    Botao.BAIXO: (pygame.K_DOWN,),
    Botao.PULO: (pygame.K_z,),
    Botao.TIRO: (pygame.K_x,),
    Botao.DASH: (pygame.K_c,),
    Botao.EX: (pygame.K_v,),
    Botao.TRAVAR: (pygame.K_LSHIFT, pygame.K_RSHIFT),
    Botao.TROCAR: (pygame.K_TAB,),
}

BOTOES_CONTROLE: Mapping[Botao, tuple[int, ...]] = {
    Botao.ESQUERDA: (pygame.CONTROLLER_BUTTON_DPAD_LEFT,),
    Botao.DIREITA: (pygame.CONTROLLER_BUTTON_DPAD_RIGHT,),
    Botao.CIMA: (pygame.CONTROLLER_BUTTON_DPAD_UP,),
    Botao.BAIXO: (pygame.CONTROLLER_BUTTON_DPAD_DOWN,),
    Botao.PULO: (pygame.CONTROLLER_BUTTON_A,),
    Botao.TIRO: (pygame.CONTROLLER_BUTTON_X,),
    Botao.EX: (pygame.CONTROLLER_BUTTON_B,),
    Botao.TROCAR: (pygame.CONTROLLER_BUTTON_Y,),
    Botao.DASH: (pygame.CONTROLLER_BUTTON_RIGHTSHOULDER,),
    Botao.TRAVAR: (pygame.CONTROLLER_BUTTON_LEFTSHOULDER,),
}

# Eixos vão de -32768 a 32767; metade do curso conta como "apertado".
LIMIAR_EIXO = 16384


class Teclas(Protocol):
    def __getitem__(self, tecla: int) -> bool: ...


class ControleDeJogo(Protocol):
    def get_button(self, botao: int) -> bool: ...
    def get_axis(self, eixo: int) -> int: ...


def comandos_do_teclado(teclas: Teclas) -> Comandos:
    return frozenset(b for b, codigos in TECLAS.items() if any(teclas[c] for c in codigos))


def comandos_do_controle(controle: ControleDeJogo) -> Comandos:
    botoes = {
        b for b, codigos in BOTOES_CONTROLE.items() if any(controle.get_button(c) for c in codigos)
    }
    x = controle.get_axis(pygame.CONTROLLER_AXIS_LEFTX)
    y = controle.get_axis(pygame.CONTROLLER_AXIS_LEFTY)
    if x <= -LIMIAR_EIXO:
        botoes.add(Botao.ESQUERDA)
    elif x >= LIMIAR_EIXO:
        botoes.add(Botao.DIREITA)
    if y <= -LIMIAR_EIXO:
        botoes.add(Botao.CIMA)
    elif y >= LIMIAR_EIXO:
        botoes.add(Botao.BAIXO)
    if controle.get_axis(pygame.CONTROLLER_AXIS_TRIGGERRIGHT) >= LIMIAR_EIXO:
        botoes.add(Botao.TIRO)
    return frozenset(botoes)


def e_pausa(evento: pygame.Event) -> bool:
    """Esc no teclado ou Start no controle."""
    if evento.type == pygame.KEYDOWN:
        return evento.key == pygame.K_ESCAPE
    if evento.type == pygame.CONTROLLERBUTTONDOWN:
        return evento.button == pygame.CONTROLLER_BUTTON_START
    return False


class Entrada:
    """Lê o teclado e os controles conectados a cada passo."""

    def __init__(self) -> None:
        sdl_controle.init()
        self.controles: list[sdl_controle.Controller] = []
        self.reconectar()

    def reconectar(self) -> None:
        self.controles = [
            sdl_controle.Controller(indice)
            for indice in range(sdl_controle.get_count())
            if sdl_controle.is_controller(indice)
        ]

    def tratar_evento(self, evento: pygame.Event) -> None:
        if evento.type in (pygame.CONTROLLERDEVICEADDED, pygame.CONTROLLERDEVICEREMOVED):
            self.reconectar()

    def ler(self) -> Comandos:
        comandos = set(comandos_do_teclado(pygame.key.get_pressed()))
        for controle in self.controles:
            comandos |= comandos_do_controle(controle)
        return frozenset(comandos)
