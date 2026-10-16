# Triagem (CupEco)

Python 3.11+ com pygame-ce. Código em `src/cupeco/`, testes em `tests/`. Idioma do projeto: português (código, commits, LOG, README). Decisões, escopo e roteiro estão no `briefing.md`.

## Fluxo obrigatório

Siga o [CONTRIBUTING.md](CONTRIBUTING.md). Em resumo, a cada mudança:

1. Trabalhe em uma branch (`feat/...`, `fix/...`), nunca na `main`.
2. Escreva ou ajuste testes. Regras ficam em `src/cupeco/dominio/` (sem pygame), com simulação em passo fixo e semente (D8).
3. Rode `python -m ruff check .`, `python -m ruff format --check .` e `python -m pytest`; só avance se passarem.
4. Abra o jogo para quem pediu testar antes do commit.
5. Adicione uma entrada **no final** do `LOG.md`, no modelo descrito no topo dele (horário local, o quê e por quê, arquivos, testes antes/depois, o que foi testado à mão).
6. Faça **um commit por arquivo**, com mensagem Conventional Commits em português. Ordem: código, testes, docs, LOG por último.
7. Não use `git add .` nem `git add -A`; adicione arquivo por arquivo.

## Cuidados

- A pasta de usuário (`C:\Users\joaov`) também é um repositório git: confira `git rev-parse --show-toplevel` antes de commitar.
- Cuphead é referência só de gênero e de ritmo (D11): nunca copie nem guarde no repositório personagens, sprites, cenários, sons, textos ou nomes de outros jogos.
- A arte é criada como código em `ferramentas/arte/` e gerada por `ferramentas/gerar_*.py` (D10); não edite os binários de `assets/` à mão. Geradores determinísticos, com semente e versões fixas.
- Conteúdo segue os princípios C1 a C8 do briefing e os checklists do CONTRIBUTING: todo fato com fonte (busca pela Consensus + pesquisa própria, de preferência em português, fontes confiáveis, nunca livros); na dúvida sobre um fato, pergunte em vez de inventar.
- Acessibilidade: nenhuma informação só por cor (D15), no máximo 3 flashes por segundo, todo ataque com aviso.
- Decisões de produto e de gosto (nomes, versão, estilo, dificuldade, publicar) são do João: pergunte.
- Não faça merge, push na `main`, tag nem release sem pedido explícito.
