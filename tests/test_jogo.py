import pygame

from cupeco.__main__ import main
from cupeco.config import ALTURA_TELA, LARGURA_TELA
from cupeco.estados.base import Estado
from cupeco.estados.titulo import EstadoTitulo


def test_janela_usa_a_resolucao_logica(jogo):
    assert jogo.tela.get_size() == (LARGURA_TELA, ALTURA_TELA)


def test_esc_na_tela_de_titulo_encerra_sem_erro(jogo):
    jogo.trocar_estado(EstadoTitulo(jogo))
    pygame.event.post(pygame.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    jogo.executar()
    assert not jogo.rodando
    assert not pygame.get_init()


def test_fechar_em_abre_e_fecha_sozinho():
    main(["--fechar-em", "0.2"])
    assert not pygame.get_init()


class EstadoContador(Estado):
    """Conta os passos de simulação e encerra o jogo depois de alguns quadros desenhados."""

    def __init__(self, jogo) -> None:
        super().__init__(jogo)
        self.passos = 0
        self.quadros = 0

    def atualizar(self) -> None:
        self.passos += 1

    def desenhar(self, tela) -> None:
        self.quadros += 1
        if self.quadros == 10:
            self.jogo.encerrar()


def test_loop_avanca_a_simulacao_em_passos_fixos(jogo):
    estado = EstadoContador(jogo)
    jogo.trocar_estado(estado)
    jogo.executar()
    # Cada quadro roda de 0 a 5 passos, conforme o tempo real que passou (D8).
    assert estado.quadros == 10
    assert 0 < estado.passos <= 50
