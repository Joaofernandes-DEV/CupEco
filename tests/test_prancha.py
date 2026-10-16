from PIL import Image, ImageDraw

from ferramentas import gerar_prancha
from ferramentas.arte.letreiro import escrever, largura
from ferramentas.arte.residuos import RESIDUOS
from ferramentas.arte.traco import Pincel, Tela


def test_os_seis_residuos_da_triagem_estao_na_prancha():
    assert list(RESIDUOS) == ["papel", "plastico", "vidro", "metal", "rejeito", "perigoso"]


def _residuo(nome: str) -> Image.Image:
    tela = Tela(100, 100, escala=2)
    RESIDUOS[nome][1](Pincel(tela, origem=(50, 50)))
    return tela.reduzir()


def test_halo_separa_reciclavel_de_proibido():
    # A 41 unidades do centro, à direita, ainda há a ponta do halo serrilhado (raio 42); o
    # halo liso dos recicláveis termina antes (raio 38). A forma do halo diz "pode ou não
    # separar" (I4). Os limites toleram a suavização das bordas.
    for nome in ("papel", "plastico", "vidro", "metal"):
        assert _residuo(nome).getpixel((91, 50))[3] < 20, nome
    for nome in ("rejeito", "perigoso"):
        assert _residuo(nome).getpixel((91, 50))[3] > 200, nome


def test_residuos_se_distinguem_sem_cor():
    # Em tons de cinza (sem matiz), os seis desenhos continuam diferentes (R3).
    cinzas = {_residuo(nome).convert("LA").tobytes() for nome in RESIDUOS}
    assert len(cinzas) == len(RESIDUOS)


def test_letreiro_desenha_os_acentos_do_portugues():
    imagem = Image.new("RGB", (900, 60), "white")
    desenho = ImageDraw.Draw(imagem)
    escrever(desenho, (5, 5), "Água, cão, pé, você, à, aí, só, pôr, põe, útil, ação", 30, "black")
    assert largura("ação", 30) > 0
    # Os acentos acrescentam tinta além das letras-base.
    sem_acento = Image.new("RGB", (900, 60), "white")
    escrever(
        ImageDraw.Draw(sem_acento),
        (5, 5),
        "Agua, cao, pe, voce, a, ai, so, por, poe, util, acao",
        30,
        "black",
    )
    assert imagem.convert("L").histogram()[0:128] != sem_acento.convert("L").histogram()[0:128]


def test_prancha_e_gerada_no_tamanho_certo_e_sempre_igual():
    primeira = gerar_prancha.gerar()
    assert primeira.size == (gerar_prancha.LARGURA, gerar_prancha.ALTURA)
    assert primeira.tobytes() == gerar_prancha.gerar().tobytes()
