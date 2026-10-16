"""Telas da luta: título, escolha de modo, luta, derrota e vitória (sem janela)."""

import pygame
import pytest

from cupeco.__main__ import analisar_argumentos, main, preparar_jogo
from cupeco.dominio.chefe import carregar_chefe
from cupeco.dominio.comandos import NENHUM
from cupeco.dominio.fatos import Fonte, Mensagem, TipoFonte
from cupeco.dominio.jogador import Jogador
from cupeco.dominio.modos import Modo
from cupeco.estados.escolha_modo import EstadoEscolhaModo
from cupeco.estados.luta import EstadoLuta, Luta
from cupeco.estados.resultado import QUADROS_DE_ESPERA, EstadoDerrota, EstadoVitoria
from cupeco.estados.titulo import EstadoTitulo
from cupeco.ui.desenho import FUNDO, Desenho


def tecla(codigo):
    return pygame.Event(pygame.KEYDOWN, key=codigo)


def lutar(jogo, modo=Modo.NORMAL, tentativa=1):
    estado = EstadoLuta(jogo, Luta(modo=modo, semente=1, tentativa=tentativa), lambda: NENHUM)
    jogo.trocar_estado(estado)
    return estado


def perder(jogo, estado):
    estado.batalha.jogador.vida = 1
    estado.batalha.jogador.tocar_perigo()
    for _ in range(40):
        jogo.estado.atualizar()
    assert isinstance(jogo.estado, EstadoDerrota)
    return jogo.estado


def vencer(jogo, estado):
    chefe = estado.chefe
    while not chefe.derrotado:
        estado._reagir(chefe.levar_dano(chefe.vida))
        while chefe.em_transicao:
            estado.atualizar()
    for _ in range(40):
        jogo.estado.atualizar()
    assert isinstance(jogo.estado, EstadoVitoria)
    return jogo.estado


def esperar_e_confirmar(jogo, estado, *teclas):
    for _ in range(QUADROS_DE_ESPERA):
        estado.atualizar()
    for codigo in (*teclas, pygame.K_RETURN):
        estado.tratar_evento(tecla(codigo))


# --- título e modo -------------------------------------------------------------------


@pytest.mark.parametrize(("descer", "modo"), [(0, Modo.NORMAL), (1, Modo.SIMPLES)])
def test_titulo_leva_a_escolha_de_modo_e_a_luta(jogo, descer, modo):
    jogo.trocar_estado(EstadoTitulo(jogo))
    jogo.estado.desenhar(jogo.tela)
    jogo.estado.tratar_evento(tecla(pygame.K_RETURN))
    assert isinstance(jogo.estado, EstadoEscolhaModo)
    for _ in range(descer):
        jogo.estado.tratar_evento(tecla(pygame.K_DOWN))
    jogo.estado.desenhar(jogo.tela)
    jogo.estado.tratar_evento(tecla(pygame.K_RETURN))
    assert isinstance(jogo.estado, EstadoLuta)
    assert jogo.estado.luta.modo is modo
    assert jogo.estado.chefe.vida == {Modo.NORMAL: 2000, Modo.SIMPLES: 1400}[modo]


def test_escolha_de_modo_volta_ao_titulo(jogo):
    jogo.trocar_estado(EstadoEscolhaModo(jogo))
    jogo.estado.tratar_evento(tecla(pygame.K_ESCAPE))
    assert isinstance(jogo.estado, EstadoTitulo)


def test_sair_no_menu_do_titulo(jogo):
    jogo.trocar_estado(EstadoTitulo(jogo))
    jogo.rodando = True
    jogo.estado.tratar_evento(tecla(pygame.K_UP))  # da primeira opção para a última
    jogo.estado.tratar_evento(tecla(pygame.K_RETURN))
    assert not jogo.rodando


# --- a luta --------------------------------------------------------------------------


def test_luta_na_arena_do_chefe():
    assert carregar_chefe("dom_obsolescencio").arena == "dom"


@pytest.mark.parametrize("modo", list(Modo))
def test_as_3_fases_rodam_e_sao_desenhadas(jogo, modo):
    estado = lutar(jogo, modo)
    estado.batalha.jogador.vida = 1_000_000  # só para a Dara aguentar o teste inteiro
    fases = []
    for fase in range(3):
        for quadro in range(900):
            estado.atualizar()
            if quadro % 3 == 0:
                estado.desenhar(jogo.tela)
        fases.append(estado.chefe.fase)
        if fase < 2:
            estado._reagir(estado.chefe.levar_dano(estado.chefe.vida))
            assert estado.faixa is not None and estado.faixa[0].startswith(f"Fase {fase + 2}")
            while estado.chefe.em_transicao:
                estado.atualizar()
                estado.desenhar(jogo.tela)
    assert fases == [0, 1, 2]
    assert estado.batalha.quadro > 2700


def test_vida_do_chefe_nao_aparece_na_tela(jogo, monkeypatch):
    estado = lutar(jogo)
    textos = []
    original = Desenho.texto

    def anotar(self, tela, texto, *args, **kwargs):
        textos.append(texto)
        return original(self, tela, texto, *args, **kwargs)

    monkeypatch.setattr(Desenho, "texto", anotar)
    estado.chefe.levar_dano(150)
    for _ in range(60):
        estado.atualizar()
    estado.tratar_evento(tecla(pygame.K_F1))  # sem --depurar, não faz nada
    estado.desenhar(jogo.tela)
    vida = str(estado.chefe.vida)
    assert not any(vida in texto or "vida" in texto.lower() for texto in textos)


def test_f1_e_f2_so_com_depurar(jogo):
    estado = lutar(jogo)
    estado.tratar_evento(tecla(pygame.K_F2))
    assert estado.chefe.fase == 0 and not estado.mostrar_caixas
    jogo.depurar = True
    estado.tratar_evento(tecla(pygame.K_F1))
    estado.tratar_evento(tecla(pygame.K_F2))
    assert estado.mostrar_caixas and estado.chefe.fase == 1
    assert estado.faixa[0] == "Fase 2: Enxame Descontinuado"
    estado.atualizar()
    estado.desenhar(jogo.tela)


def test_pausa_congela_e_reiniciar_comeca_outra_tentativa(jogo):
    estado = lutar(jogo)
    estado.atualizar()
    estado.tratar_evento(tecla(pygame.K_ESCAPE))
    quadro = estado.batalha.quadro
    for _ in range(30):
        estado.atualizar()
    assert estado.batalha.quadro == quadro
    estado.desenhar(jogo.tela)
    estado.tratar_evento(tecla(pygame.K_DOWN))
    estado.tratar_evento(tecla(pygame.K_RETURN))  # "Reiniciar"
    novo = jogo.estado
    assert isinstance(novo, EstadoLuta) and novo is not estado
    assert novo.luta.tentativa == 2 and novo.batalha.semente == estado.batalha.semente + 1


def test_pausa_sair_volta_ao_titulo(jogo):
    estado = lutar(jogo)
    estado.tratar_evento(tecla(pygame.K_ESCAPE))
    estado.tratar_evento(tecla(pygame.K_UP))
    estado.tratar_evento(tecla(pygame.K_RETURN))
    assert isinstance(jogo.estado, EstadoTitulo)


def test_aviso_da_bateria_fala_em_pilhas_e_baterias(jogo):
    from cupeco.dominio.jogador import EventoJogador
    from cupeco.dominio.materiais import Material

    estado = lutar(jogo)
    estado.batalha.jogador.ultimo_residuo = Material.PERIGOSO
    estado._reagir([EventoJogador.TRIAGEM_PROIBIDA])
    assert estado.aviso[0].startswith("Pilhas e baterias são resíduos perigosos")


def test_dara_pisca_no_maximo_3_vezes_por_segundo(jogo):
    dara = Jogador(600.0, 640.0)
    dara._invencivel = 1_000  # invencível o segundo inteiro
    desenho, visivel = Desenho(), []
    centro = tuple(round(c) for c in dara.corpo.caixa.centro)
    for quadro in range(60):
        jogo.tela.fill(FUNDO)
        desenho.dara(jogo.tela, dara, quadro)
        visivel.append(tuple(jogo.tela.get_at(centro))[:3] != FUNDO)
    sumidas = sum(1 for a, b in zip(visivel, visivel[1:], strict=False) if a and not b)
    assert 1 <= sumidas <= 3


# --- derrota -------------------------------------------------------------------------


def test_derrota_mostra_o_progresso_e_tenta_de_novo_na_hora(jogo):
    estado = lutar(jogo)
    estado.chefe.levar_dano(1500)  # para no limite da fase 2
    derrota = perder(jogo, estado)
    assert derrota.batalha.chefe.progresso > 0
    derrota.desenhar(jogo.tela)
    derrota.tratar_evento(tecla(pygame.K_RETURN))  # cedo demais: ignorado
    assert jogo.estado is derrota
    esperar_e_confirmar(jogo, derrota)
    assert isinstance(jogo.estado, EstadoLuta) and jogo.estado.luta.tentativa == 2
    assert jogo.estado.batalha.quadro == 0


def test_derrota_trocar_de_modo(jogo):
    derrota = perder(jogo, lutar(jogo, Modo.SIMPLES))
    esperar_e_confirmar(jogo, derrota, pygame.K_DOWN)
    assert isinstance(jogo.estado, EstadoEscolhaModo)


def test_mensagens_nao_repetem_entre_tentativas(jogo):
    vistas = []
    estado = lutar(jogo)
    for _ in range(5):
        derrota = perder(jogo, estado)
        assert not derrota.mensagem.e_fato  # ainda não há fatos: só dicas (D35)
        vistas.append(derrota.mensagem.id)
        esperar_e_confirmar(jogo, derrota)
        estado = jogo.estado
        estado._ler = lambda: NENHUM
    assert len(set(vistas)) == 5


def test_mensagem_com_fonte_mostra_a_fonte(jogo):
    derrota = perder(jogo, lutar(jogo))
    fonte = Fonte("Documento de teste", "Autor de teste", 2020, TipoFonte.LEGISLACAO, "2026-10-16")
    derrota.mensagem = Mensagem("teste", "Fato de teste.", fonte)
    derrota.desenhar(jogo.tela)


# --- vitória -------------------------------------------------------------------------


@pytest.mark.parametrize("modo", list(Modo))
def test_vitoria_mostra_a_nota_com_o_modo(jogo, modo):
    vitoria = vencer(jogo, lutar(jogo, modo))
    assert vitoria.nota.modo is modo and vitoria.nota.letra in {"A+", "A", "B", "C", "D"}
    vitoria.desenhar(jogo.tela)
    esperar_e_confirmar(jogo, vitoria)  # "Jogar de novo"
    assert isinstance(jogo.estado, EstadoLuta) and jogo.estado.luta.modo is modo


def test_vitoria_sair_para_o_titulo(jogo):
    vitoria = vencer(jogo, lutar(jogo))
    esperar_e_confirmar(jogo, vitoria, pygame.K_DOWN)
    assert isinstance(jogo.estado, EstadoTitulo)


# --- linha de comando ----------------------------------------------------------------


def test_luta_e_modo_na_linha_de_comando():
    jogo = preparar_jogo(analisar_argumentos(["--luta", "dom_obsolescencio", "--modo", "simples"]))
    try:
        assert isinstance(jogo.estado, EstadoLuta)
        assert jogo.estado.luta.modo is Modo.SIMPLES and not jogo.depurar
    finally:
        pygame.quit()


def test_depurar_na_linha_de_comando():
    jogo = preparar_jogo(analisar_argumentos(["--luta", "dom_obsolescencio", "--depurar"]))
    try:
        assert jogo.depurar and jogo.estado.luta.modo is Modo.NORMAL
    finally:
        pygame.quit()


def test_luta_abre_e_fecha_sozinha():
    main(["--luta", "dom_obsolescencio", "--fechar-em", "0.3"])
    assert not pygame.get_init()


def test_chefe_desconhecido_na_linha_de_comando():
    with pytest.raises(SystemExit):
        analisar_argumentos(["--luta", "baron"])
