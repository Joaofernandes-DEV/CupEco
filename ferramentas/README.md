# Ferramentas

Scripts de apoio que **geram** arquivos do projeto. Nenhum binário de `src/cupeco/assets/` é editado à mão: tudo sai daqui e pode ser recriado e conferido (princípio 4, D10 do [briefing](../briefing.md)).

A arte do jogo é criada como código: personagens e cenários ficam descritos em `ferramentas/arte/` (formas, curvas e poses) e os geradores desenham os quadros e montam os spritesheets.

## O que já existe

| Arquivo | O que faz |
|---------|-----------|
| `arte/traco.py` | Curvas suaves, membros de "mangueira", formas com contorno, olhos *pie-cut* e a "linha viva" |
| `arte/paleta.py` | Cores: as dos materiais (CONAMA 275/2001) e as dos personagens e cenários |
| `arte/personagens/` | A Dara (esqueleto de poses) e o Canhão de Triagem |
| `arte/residuos.py` | Os 6 resíduos da Triagem, com cor, silhueta e marca |
| `arte/cenarios/` | Aterrópolis |
| `arte/efeitos.py` | Efeito de filme: tom desbotado, grão e vinheta |
| `arte/letreiro.py` | Texto com acentos do português sobre a fonte embutida do Pillow |
| `gerar_prancha.py` | Gera a prancha de estilo em `docs/prancha-estilo.png` (D19) |

## Convenções

- Um gerador por tipo de asset: `gerar_<o_que>.py` (ex.: `gerar_sprites.py`, `gerar_sons.py`).
- **Determinístico:** a mesma execução gera sempre os mesmos arquivos. Se houver sorteio (como a "linha viva" do traço), use semente fixa.
- Bibliotecas de geração (como o Pillow) ficam em versão fixa, para o resultado ser idêntico em qualquer máquina e no CI.
- Ao mudar um gerador, regenere e confira com `git status` se só mudaram os arquivos esperados. Os outros devem sair idênticos.
- As dependências das ferramentas ficam no extra `[ferramentas]` (`python -m pip install -e ".[dev,ferramentas]"`).
- Rode como módulo, a partir da raiz do repositório, com o ambiente virtual ativo:

  ```bash
  python -m ferramentas.gerar_prancha
  ```

A prancha de estilo entra na Fase 1 (D19), os spritesheets e os sons na Fase 3 e o empacotador do executável na Fase 8. Veja o roteiro no [briefing.md](../briefing.md).
