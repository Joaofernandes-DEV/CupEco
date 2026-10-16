# Ferramentas

Scripts de apoio que **geram** arquivos do projeto. Nenhum binário de `src/cupeco/assets/` é editado à mão: tudo sai daqui e pode ser recriado e conferido (princípio 4, D10 do [briefing](../briefing.md)).

A arte do jogo é criada como código: personagens e cenários ficam descritos em `ferramentas/arte/` (formas, curvas e poses) e os geradores desenham os quadros e montam os spritesheets.

## Convenções

- Um gerador por tipo de asset: `gerar_<o_que>.py` (ex.: `gerar_sprites.py`, `gerar_sons.py`).
- **Determinístico:** a mesma execução gera sempre os mesmos arquivos. Se houver sorteio (como a "linha viva" do traço), use semente fixa.
- Bibliotecas de geração (como o Pillow) ficam em versão fixa, para o resultado ser idêntico em qualquer máquina e no CI.
- Ao mudar um gerador, regenere e confira com `git status` se só mudaram os arquivos esperados. Os outros devem sair idênticos.
- Rode a partir da raiz do repositório, com o ambiente virtual ativo:

  ```bash
  python ferramentas/gerar_sprites.py
  ```

A prancha de estilo entra na Fase 1 (D19), os geradores de arte e som na Fase 3 e o empacotador do executável na Fase 8. Veja o roteiro no [briefing.md](../briefing.md).
