"""Ponto de entrada.

`python -m cupeco [--luta ID [--modo simples] | --arena] [--semente N] [--depurar]
[--fechar-em SEGUNDOS]`.
"""

import argparse
from collections.abc import Sequence

import pygame

from cupeco import __version__
from cupeco.config import TITULO
from cupeco.dominio.chefe import listar_chefes
from cupeco.dominio.modos import Modo
from cupeco.estados.arena import SEMENTE_PADRAO, EstadoArena
from cupeco.estados.luta import EstadoLuta, Luta
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
    inicio = parser.add_mutually_exclusive_group()
    inicio.add_argument(
        "--arena", action="store_true", help="começa direto na arena de testes, sem o título"
    )
    inicio.add_argument(
        "--luta",
        choices=listar_chefes(),
        default=None,
        metavar="ID",
        help=f"começa direto na luta contra um chefe ({', '.join(listar_chefes())})",
    )
    parser.add_argument(
        "--modo",
        choices=[m.value for m in Modo],
        default=Modo.NORMAL.value,
        help="modo da luta (com --luta)",
    )
    parser.add_argument(
        "--depurar",
        action="store_true",
        help="na luta, F1 mostra as caixas e a vida do chefe e F2 pula para a próxima fase",
    )
    parser.add_argument(
        "--semente",
        type=int,
        default=SEMENTE_PADRAO,
        metavar="N",
        help="semente dos sorteios (a mesma semente repete a mesma luta)",
    )
    return parser.parse_args(argumentos)


def preparar_jogo(opcoes: argparse.Namespace) -> Jogo:
    jogo = Jogo()
    jogo.depurar = opcoes.depurar
    if opcoes.arena:
        jogo.trocar_estado(EstadoArena(jogo, semente=opcoes.semente))
    elif opcoes.luta:
        luta = Luta(chefe=opcoes.luta, modo=Modo(opcoes.modo), semente=opcoes.semente)
        jogo.trocar_estado(EstadoLuta(jogo, luta))
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
