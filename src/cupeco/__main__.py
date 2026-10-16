"""Ponto de entrada: `python -m cupeco [--arena] [--semente N] [--fechar-em SEGUNDOS]`."""

import argparse
from collections.abc import Sequence

import pygame

from cupeco import __version__
from cupeco.config import TITULO
from cupeco.estados.arena import SEMENTE_PADRAO, EstadoArena
from cupeco.estados.titulo import EstadoTitulo
from cupeco.jogo import Jogo


def analisar_argumentos(argumentos: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="cupeco", description=TITULO)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--fechar-em",
        type=float,
        default=None,
        metavar="SEGUNDOS",
        help="fecha o jogo sozinho depois desse tempo (teste automático do executável)",
    )
    parser.add_argument(
        "--arena", action="store_true", help="começa direto na arena de testes, sem o título"
    )
    parser.add_argument(
        "--semente",
        type=int,
        default=SEMENTE_PADRAO,
        metavar="N",
        help="semente dos sorteios da arena (a mesma semente repete a mesma luta)",
    )
    return parser.parse_args(argumentos)


def preparar_jogo(opcoes: argparse.Namespace) -> Jogo:
    jogo = Jogo()
    if opcoes.arena:
        jogo.trocar_estado(EstadoArena(jogo, semente=opcoes.semente))
    else:
        jogo.trocar_estado(EstadoTitulo(jogo))
    if opcoes.fechar_em is not None:
        # Um evento QUIT agendado: o jogo encerra pelo caminho normal, como se a janela fechasse.
        pygame.time.set_timer(pygame.Event(pygame.QUIT), round(opcoes.fechar_em * 1000), loops=1)
    return jogo


def main(argumentos: Sequence[str] | None = None) -> None:
    preparar_jogo(analisar_argumentos(argumentos)).executar()


if __name__ == "__main__":
    main()
