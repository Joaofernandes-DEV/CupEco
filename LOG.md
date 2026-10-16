# Diário de Bordo — Triagem (CupEco)

Registro cronológico de **todas** as alterações feitas no projeto. Cada entrada traz a data, o que foi feito, os arquivos afetados e o motivo da mudança.

## Como registrar

- Uma entrada por mudança (ou por PR), **a mais recente no final**.
- Data e horário no formato `AAAA-MM-DD HH:MM` (horário local), no momento em que a mudança foi concluída.
- Descreva **o quê** mudou e **por quê**; o "como" detalhado fica no código e nos commits.
- Informe o número de testes antes e depois, e o que foi testado à mão (e o que ficou para conferir).
- Se a mudança trata de um item do [briefing.md](briefing.md), cite o código (ex.: `J3`, `R5`, `C1`).
- Experimentos rejeitados também entram: registre a tentativa e a volta.

Modelo:

```markdown
### AAAA-MM-DD HH:MM — Título curto

**Feito:**
- O que mudou (o "como" detalhado fica no código e nos commits).

**Arquivos:** `caminho/arquivo.py`, `tests/test_x.py` (novo), `LOG.md`.

**Motivo / observações:**
- Por que mudou, item do briefing resolvido (ex.: `B3`), limitações conhecidas e próximos passos.
```

---

## Entradas

### 2026-10-16 12:46 — Fase 0: fundação do projeto

**Feito:**
- Concepção de game design fechada com o João: protagonistas Dara e Pet, Triagem híbrida (variante C), três chefes com 3 fases cada, Modo Simples e estilo *rubber hose* com personagens originais.
- `briefing.md` da V1 escrito e revisado pelo João: visão geral e os 10 princípios, riscos R1 a R13, estrutura do código, interface I1 a I13, funcionalidades J1 a J18, princípios de conteúdo C1 a C8, decisões D1 a D22, escopo e roteiro em 9 fases. Respostas da revisão: arte criada pelo Claude como código (P1, D10, D19), trilha gerada por script (P2), revisão externa (P3, D22), cidade Aterrópolis (P5, D21) e título "Triagem" com CupEco como codinome (P6, D20). O prazo (P4) segue em aberto.
- Repositório local criado na pasta `CupEco` (`git init`, `origin` no GitHub), separado do repositório da pasta de usuário (D1, R13).
- Configuração: `pyproject.toml` (versão 0.1.0, pygame-ce, extra `[dev]` com pytest e ruff, ruff com `line-length = 100` e regras `E, F, W, I, UP, B, SIM, N`), `.gitignore` e licenças (MIT para o código, CC BY 4.0 para o conteúdo).
- Esqueleto do jogo em `src/cupeco/`: janela de 1280×720 com `pygame.SCALED` (D4), loop com troca de estados e **simulação em passo fixo de 1/60 s** com limite de 5 passos por quadro (`passo_fixo.py`, D8), tela de título provisória (Esc fecha) e a opção `--fechar-em SEGUNDOS`.
- Pastas `dominio/` (regras puras, sem pygame), `estados/`, `ui/`, `assets/` e `ferramentas/` (com as convenções dos geradores).
- CI (`ci.yml`): ruff e pytest no Ubuntu 24.04 (Python 3.11, 3.12 e 3.13) e no Windows (3.11), com `fail-fast: false`.
- Documentação: `README.md`, `CONTRIBUTING.md` (com os checklists de conteúdo e de acessibilidade) e `CLAUDE.md`.

**Arquivos:** `.gitignore`, `LICENSE`, `LICENCA-CONTEUDO.md`, `pyproject.toml`, `src/cupeco/__init__.py`, `src/cupeco/__main__.py`, `src/cupeco/config.py`, `src/cupeco/passo_fixo.py`, `src/cupeco/jogo.py`, `src/cupeco/estados/__init__.py`, `src/cupeco/estados/base.py`, `src/cupeco/estados/titulo.py`, `src/cupeco/dominio/__init__.py`, `src/cupeco/ui/__init__.py`, `src/cupeco/assets/.gitkeep`, `ferramentas/README.md`, `tests/conftest.py`, `tests/test_versao.py`, `tests/test_jogo.py`, `tests/test_passo_fixo.py`, `tests/test_dominio.py`, `.github/workflows/ci.yml`, `README.md`, `CONTRIBUTING.md`, `CLAUDE.md`, `briefing.md`, `LOG.md` (todos novos).

**Motivo / observações:**
- Regra 1: o briefing vem antes do código; a Fase 0 deixa o projeto abrindo, testado e com CI (Regra 2).
- Testes: 0 → 10 (versão, janela na resolução lógica, Esc encerra, `--fechar-em`, loop em passos fixos, quatro casos do relógio de passo fixo e domínio sem pygame).
- Testado localmente: `ruff check`, `ruff format --check` e `pytest` passando no Windows com Python 3.11.8 e pygame-ce 2.5.8; captura da tela de título conferida (acentos de "Aterrópolis" corretos). Falta o teste do João abrindo o jogo.
- Próximos passos: commits por arquivo, push, PR da Fase 0, CI verde no GitHub e proteção da `main`.

### 2026-10-16 12:51 — Fase 0 concluída: CI verde e `main` protegida

**Feito:**
- Commit inicial vazio na `main`; a Fase 0 entrou pelo PR #1 (`chore/fase-0-fundacao`, 27 commits, um por arquivo), com merge commit, e a branch foi apagada.
- CI verde no PR #1 nos 4 jobs: Ubuntu 24.04 com Python 3.11, 3.12 e 3.13 e Windows com Python 3.11.
- Proteção da `main` no GitHub: Pull Request obrigatório (0 aprovações), os 4 checks `Lint e testes (…)` exigidos, branch em dia com a `main`, sem force-push e sem exclusão; o administrador pode ignorar em emergência.
- Auto-fix do app ligado para o PR #1, a pedido do João.
- Fase 0 marcada com ✅ no roteiro do briefing; situação atualizada no briefing e no README.

**Arquivos:** `briefing.md`, `README.md`, `LOG.md`.

**Motivo / observações:**
- Fecha a Fase 0 (Regras 2 e 7). Testes: 10 → 10 (só documentação).
- Ao mudar a matriz do CI, atualizar a lista de checks exigidos na proteção da `main`.
- Próximo: Fase 1 (núcleo: física, Dara, armas, Triagem, Medidor e dano no domínio, arena de testes e prancha de estilo, D19).

### 2026-10-16 12:55 — Plano da Fase 1

**Feito:**
- Plano da Fase 1 aprovado pelo João e registrado no briefing (seção 10.1): 10 PRs, da prancha de estilo à arena de testes.
- Novas decisões técnicas: números e sorteio determinísticos (D23), comandos como botões segurados e replays (D24), Medidor em pontos inteiros (D25), valores de jogo em TOML com validação estrita (D26) e Pillow fixo no extra `[ferramentas]` (D27).
- Situação do briefing atualizada: Fase 1 em andamento.

**Arquivos:** `briefing.md`, `LOG.md`.

**Motivo / observações:**
- Regra 1 aplicada à Fase 1: o plano vem antes do código. Testes: 10 → 10 (só documentação).
- Próximo: PR 1, `feat/prancha-de-estilo` (D19).
