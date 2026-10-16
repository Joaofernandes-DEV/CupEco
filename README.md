# Triagem (CupEco)

[![CI](https://github.com/Joaofernandes-DEV/CupEco/actions/workflows/ci.yml/badge.svg)](https://github.com/Joaofernandes-DEV/CupEco/actions/workflows/ci.yml)

Jogo 2D de ação contra chefões, no estilo dos desenhos animados dos anos 1930, sobre reciclagem, resíduos e meio ambiente. Em **Aterrópolis**, uma megacidade brasileira fictícia onde a coleta de lixo parou, **Dara**, uma catadora de 16 anos, e o robô **Pet** enfrentam os **Rejeitos**: monstros nascidos do descarte, como o Dom Obsolescêncio (lixo eletrônico), o Barão Fuligem (poluição industrial) e o Leviatã de Plástico (plástico nos oceanos).

O jogo ensina pela mecânica:

- o parry, chamado **Triagem**, só funciona quando o jogador separa os resíduos pela cor certa da coleta seletiva (resolução CONAMA 275/2001);
- rejeitos e resíduos perigosos (pilhas, baterias) não podem ser "separados";
- cada derrota e cada vitória mostram um **"Você sabia?"** com fonte;
- a história lembra que reciclar é o último recurso: antes vêm **repensar, recusar e reduzir**.

É difícil como os clássicos do gênero, mas tem um **Modo Simples** para quem está começando, com todas as fases de cada chefe.

Projeto de extensão da UNIP. Público: 10 anos ou mais. "CupEco" é o codinome do repositório; o título do jogo é **Triagem**.

## Situação

🚧 **Em desenvolvimento.** Fase 0 (fundação) concluída: a janela abre com uma tela de título provisória. Próxima: Fase 1 (Dara e o combate no domínio, arena de testes e prancha de estilo). O roteiro completo, as decisões e o escopo da V1 estão no [briefing.md](briefing.md); o histórico de cada mudança está no [LOG.md](LOG.md).

O executável para Windows será publicado nas [releases](https://github.com/Joaofernandes-DEV/CupEco/releases) na entrega da V1.

## Como rodar (código-fonte)

Requer Python 3.11 ou mais recente.

```bash
git clone https://github.com/Joaofernandes-DEV/CupEco.git
cd CupEco
python -m venv .venv
```

Ative o ambiente virtual (Windows: `.venv\Scripts\activate`; Linux/macOS: `source .venv/bin/activate`) e rode:

```bash
python -m pip install -e ".[dev,ferramentas]"
python -m cupeco
```

`Esc` fecha o jogo. Para um teste rápido que fecha sozinho: `python -m cupeco --fechar-em 2`.

## Como desenvolver

O fluxo completo está no [CONTRIBUTING.md](CONTRIBUTING.md). Antes de cada commit:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Estrutura: regras puras em `src/cupeco/dominio/` (sem pygame), telas em `estados/`, componentes visuais em `ui/`, arte e sons gerados por scripts em `ferramentas/` e testes em `tests/`. A simulação roda em passos fixos de 1/60 s (`passo_fixo.py`), o que deixa cada luta determinística e reproduzível.

## Licença

- **Código:** [MIT](LICENSE).
- **Conteúdo** (textos, fatos, personagens, arte e sons): [CC BY 4.0](LICENCA-CONTEUDO.md). Pode ser usado em sala de aula e adaptado, desde que se dê o crédito.
