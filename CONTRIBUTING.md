# Como contribuir

O fluxo é sempre o mesmo: **branch → mudança pequena → teste → entrada no LOG → um commit por arquivo → Pull Request → merge com o CI verde**.

## 1. Preparar o ambiente

```bash
git clone https://github.com/Joaofernandes-DEV/CupEco.git
cd CupEco
python -m venv .venv
```

Ative o ambiente virtual (Windows: `.venv\Scripts\activate`; Linux/macOS: `source .venv/bin/activate`) e instale:

```bash
python -m pip install -e ".[dev,ferramentas]"
```

> Se o caminho da pasta tiver espaços, use aspas nos comandos. Prefira `python -m pytest` e `python -m ruff`, que funcionam mesmo com acentos no caminho.

## 2. Criar uma branch

Nunca trabalhe direto na `main`. Parta dela atualizada:

```bash
git switch main
git pull
git switch -c feat/nome-curto-da-mudanca
```

Prefixos: `feat/`, `fix/`, `docs/`, `test/`, `chore/`.

## 3. Implementar com testes

- Regras do jogo ficam em `src/cupeco/dominio/` (sem pygame) e têm teste em `tests/`.
- A simulação avança em passos fixos de 1/60 s e usa números aleatórios com semente: o mesmo comando gera sempre o mesmo resultado. Não use o relógio real nem `random` sem semente dentro do domínio.
- Valores de equilíbrio (vida, velocidade, avisos dos ataques) ficam nos dados em `src/cupeco/conteudo/`, não no código.
- Toda mudança de comportamento traz teste novo ou ajustado.
- Testes de tela rodam sem janela (`SDL_VIDEODRIVER=dummy`, já configurado em `tests/conftest.py`).
- Arte e sons são gerados por `ferramentas/gerar_*.py`. Edite o gerador e regenere; não edite os binários à mão.

Antes de seguir, rode os três comandos. Só avance se todos passarem:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

## 4. Testar de verdade

Abra o jogo (`python -m cupeco`) e jogue o que mudou, no teclado e, se mexeu em controles, no controle. Teste automático não substitui jogar. Se outra pessoa pediu a mudança, ela testa antes do commit.

## 5. Checklists de conteúdo e acessibilidade

Todo PR que cria ou altera textos, fatos, personagens, arte ou sons segue os princípios de conteúdo do [briefing.md](briefing.md) (seção 6). Antes de abrir o PR, confira:

- [ ] Todo fato tem fonte registrada nos dados, de origem confiável (órgão oficial, legislação, artigo revisado, instituição de pesquisa), e nunca de livro.
- [ ] O texto não sugere que reciclar compensa consumir sem pensar (ordem da PNRS: não gerar, reduzir, reutilizar, reciclar).
- [ ] Nenhuma pessoa, empresa, marca ou governo real aparece como vilão ou é aludido.
- [ ] Catadores e catadoras aparecem com dignidade, nunca como piada ou motivo de pena.
- [ ] O texto aponta algo que se pode fazer, sem culpar o jogador.
- [ ] Fatos na tela têm no máximo 2 frases.
- [ ] Nada foi copiado de outros jogos (personagens, sprites, cenários, sons, textos), nem guardado como referência no repositório.

E, para arte, efeitos e ataques:

- [ ] Nenhuma informação depende só de cor: cada material tem cor, ícone e silhueta.
- [ ] No máximo 3 flashes por segundo; tremor de tela e grão respeitam as opções de acessibilidade.
- [ ] Todo ataque novo tem aviso visual e sonoro antes de acontecer.

## 6. Registrar no LOG.md

Adicione **uma entrada no final** do [LOG.md](LOG.md), no modelo descrito no topo dele:

- horário local no momento em que a mudança foi concluída;
- o **quê** e o **porquê** (o "como" fica no código e nos commits);
- o número de testes antes e depois;
- o que foi testado à mão e o que ficou para conferir;
- os itens do briefing resolvidos (ex.: `J3`, `R5`).

## 7. Um commit por arquivo

Cada arquivo alterado vira um commit próprio, com mensagem curta em português no formato [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add src/cupeco/dominio/triagem.py
git commit -m "feat: aplica a regra de cores da Triagem"

git add tests/test_triagem.py
git commit -m "test: cobre a matriz completa da Triagem"

git add LOG.md
git commit -m "docs: registra a Triagem no diário de bordo"
```

- Tipos: `feat`, `fix`, `test`, `docs`, `build`, `ci`, `chore`.
- Ordem: código → testes → documentação → LOG por último.
- **Nunca** use `git add .` nem `git add -A`.

## 8. Abrir o Pull Request

```bash
git push -u origin feat/nome-curto-da-mudanca
gh pr create
```

Use esta descrição:

```markdown
## O que muda
- ...

## Como testar
`python -m pytest` e <como abrir o jogo e o que conferir>.
```

## 9. Merge

- Só com o CI verde e a branch em dia com a `main`.
- Use **merge commit** (preserva os commits por arquivo). Depois, apague a branch.
- PRs que dependem uns dos outros: abra empilhados e faça o merge na ordem. Atualize cada um (`gh pr update-branch N`) e espere o CI antes do próximo. Conflitos no `LOG.md` se resolvem mantendo a ordem cronológica.

## 10. Experimentos

Uma ideia testada e rejeitada sai por um PR próprio, e o LOG registra a tentativa e a volta.

## Versões

Versionamento semântico, publicado por tag `vX.Y.Z` pelo mantenedor, depois de um PR `chore/release-vX.Y.Z`.
