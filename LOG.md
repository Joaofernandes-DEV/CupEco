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

### 2026-10-16 13:06 — Prancha de estilo (versão 1, para aprovação)

**Feito:**
- Biblioteca de traço em `ferramentas/arte/traco.py`: curvas suaves que passam pelas âncoras, traço de pincel com pontas finas, membros de "mangueira" sem cotovelo, formas com contorno, olhos *pie-cut* e a "linha viva" (tremor com semente). Desenho em resolução 4× e redução no fim; sem seno nem cosseno (D23).
- Dara em 3 poses (parada, correndo, pulo com tiro na diagonal), com esqueleto de poses, boné da cooperativa, macacão, luvas de trabalho amarelas e botas; Canhão de Triagem com a faixa da cor ativa (D12).
- Os 6 resíduos com cor da CONAMA, silhueta e marca: halo liso nos recicláveis, halo serrilhado com selo de proibido ou de perigo no rejeito e no perigoso (I4, D15).
- Pedaço de Aterrópolis (prédios "de borracha", chaminés com fumaça, aterro, rua e poste) com efeito de filme: tom desbotado, grão e vinheta (I2).
- `letreiro.py`: acentos do português desenhados sobre a fonte embutida do Pillow, que só tem ASCII. A fonte do jogo continua para a Fase 3 (I12).
- `python -m ferramentas.gerar_prancha` gera `docs/prancha-estilo.png`. Pillow 12.3.0 fixo no extra `[ferramentas]` (D27); o CI e as instruções de instalação passam a usar `.[dev,ferramentas]`; o pytest ganha a raiz no caminho de importação.

**Arquivos:** `pyproject.toml`, `.github/workflows/ci.yml`, `ferramentas/__init__.py`, `ferramentas/arte/__init__.py`, `ferramentas/arte/traco.py`, `ferramentas/arte/paleta.py`, `ferramentas/arte/efeitos.py`, `ferramentas/arte/letreiro.py`, `ferramentas/arte/residuos.py`, `ferramentas/arte/personagens/__init__.py`, `ferramentas/arte/personagens/canhao.py`, `ferramentas/arte/personagens/dara.py`, `ferramentas/arte/cenarios/__init__.py`, `ferramentas/arte/cenarios/aterropolis.py`, `ferramentas/gerar_prancha.py` (novos), `docs/prancha-estilo.png` (gerado), `tests/test_traco.py`, `tests/test_prancha.py` (novos), `ferramentas/README.md`, `README.md`, `CONTRIBUTING.md`, `LOG.md`.

**Motivo / observações:**
- D19: validar o estilo da arte por código antes de qualquer animação (R1).
- Testes: 10 → 24 (curvas, rotação, determinismo da linha viva e do grão, halo que separa reciclável de proibido, resíduos distintos em tons de cinza, acentos do letreiro, prancha sempre igual).
- Conferido à mão pelo Claude, abrindo a imagem gerada: corrigidas as solas que pareciam rodas (a ponta da perna aparecia sob a bota), o canhão que cobria o rosto no pulo, a faixa da cor ativa pequena demais e a garrafa PET que parecia um frasco de ketchup.
- Falta a aprovação do João (D19); ajustes pedidos entram neste mesmo PR antes do merge.
- A prancha não é conferida pixel a pixel no CI; essa conferência entre sistemas entra com os spritesheets na Fase 3 (R10).

### 2026-10-16 13:12 — Dados de jogo em TOML e materiais da Triagem

**Feito:**
- Prancha de estilo **aprovada pelo João** em 2026-10-16, sem ajustes (D19); PRs #3 (plano da Fase 1) e #4 (prancha) mergeados com o CI verde.
- `dominio/dados.py`: leitor dos TOML de `src/cupeco/conteudo/` com validação estrita (D26). Converte para dataclasses (aninhadas), textos, inteiros, números, verdadeiro/falso e tuplas; chave desconhecida, faltando ou de tipo errado gera `DadosInvalidos` com o caminho da chave (ex.: `materiais.papel.cor`).
- `dominio/materiais.py`: os 6 materiais da Triagem; a classificação (reciclável, rejeito, perigoso) e quem pode ser separado é regra no código (D12); nome, cor e ícone vêm de `conteudo/materiais.toml`, com a fonte. A tabela exige cor e ícone em todos, sem repetição (D15, R3).
- Fonte conferida no texto da resolução: CONAMA nº 275, de 25/04/2001 (DOU de 19/06/2001), Anexo com azul (papel), vermelho (plástico), verde (vidro), amarelo (metal), laranja (resíduos perigosos) e cinza (rejeitos não recicláveis, misturados ou contaminados) (C1).
- A paleta da arte (`ferramentas/arte/paleta.py`) passa a ler as cores dos materiais dessa mesma tabela: uma só fonte de verdade. A prancha regenerada saiu idêntica, pixel a pixel.
- Os TOML vão junto no pacote (`package-data`).

**Arquivos:** `src/cupeco/dominio/dados.py`, `src/cupeco/dominio/materiais.py`, `src/cupeco/conteudo/__init__.py`, `src/cupeco/conteudo/materiais.toml` (novos), `ferramentas/arte/paleta.py`, `pyproject.toml`, `tests/test_dados.py`, `tests/test_materiais.py` (novos), `LOG.md`.

**Motivo / observações:**
- PR 2 do plano da Fase 1 (D15, D26). Testes: 24 → 50 (conversão e cada tipo de erro do leitor; materiais, tipos e separáveis; cor e ícone distintos; matiz de cada cor conforme a CONAMA; fonte; erros de tabela; arte e jogo com as mesmas cores).
- Sem mudança visível no jogo: nada para abrir e testar à mão neste PR.
- Próximo: PR 3, `feat/fisica`.

### 2026-10-16 13:17 — Física: caixas, gravidade e plataformas

**Feito:**
- PR #5 (dados e materiais) mergeado com o CI verde.
- `dominio/fisica.py`: `Caixa` (retângulo de colisão), `Plataforma` (sólida ou atravessável por baixo), `Corpo` (posição, velocidade e se está no chão) e `mover`, que aplica a gravidade com queda máxima e resolve a colisão um eixo de cada vez (x, depois y), devolvendo os `Contatos` do passo (chão, teto, paredes).
- Colisão por **varredura**: uma borda só bate numa plataforma se, antes do passo, estava do lado de fora dela. Um corpo rápido não atravessa chão fino, e quem sobe por dentro de uma plataforma atravessável não é puxado para cima.
- Plataformas atravessáveis: seguram só quem cai de cima, não contam como parede nem como teto, e `descer` deixa o corpo passar por elas (base para "baixo + pulo" no PR 4).
- Coordenadas em pixels lógicos, velocidades em pixels por passo, só as quatro operações (D8, D23).

**Arquivos:** `src/cupeco/dominio/fisica.py`, `tests/test_fisica.py` (novos), `LOG.md`.

**Motivo / observações:**
- PR 3 do plano da Fase 1. Testes: 50 → 69 (sobreposição de caixas, queda livre e queda máxima, pouso exato, ficar parado no chão, chão fino em queda rápida, sair da beirada, primeira plataforma do caminho, paredes dos dois lados, chão que não é parede, teto, as quatro regras da plataforma atravessável e repetibilidade).
- Sem mudança visível no jogo: a física aparece na arena de testes (PR 8).
- Próximo: PR 4, `feat/jogador-movimento`.

### 2026-10-16 13:22 — Movimento da Dara e comandos

**Feito:**
- PR #6 (física) mergeado com o CI verde.
- `dominio/comandos.py`: `Botao` e `Controle`. A interface entrega só os botões segurados em cada passo; o domínio calcula "apertou" e "soltou" comparando com o passo anterior, e a direção (opostos se anulam) (D24).
- `dominio/jogador.py` + `conteudo/jogador.toml`: a Dara corre, pula com altura variável (soltar o botão corta a subida), pula até 6 quadros depois de sair da beirada, guarda o pulo apertado até 6 quadros antes de pousar, agacha (caixa mais baixa, sem andar), trava no lugar para mirar, faz dash (velocidade fixa, sem gravidade, 1 no ar até pousar, espera entre dashes, **sem invencibilidade**, D14) e desce de plataforma atravessável com baixo + pulo (no chão sólido, baixo + pulo pula).
- Mira em 8 direções: no ar, para onde se segura; travada, as 8 (no chão, "para baixo" vira a diagonal da frente); correndo + cima, a diagonal; parada + cima, reto para cima; agachada, para a frente.
- Eventos do passo (`PULOU`, `POUSOU`, `DASH`, `DESCEU`) para a interface tocar sons e animações depois.
- `fisica.apoios`: plataformas sob os pés, usada no dash (que não tem gravidade) e no "descer da tábua".
- Parâmetros validados: positivos, agachada menor que em pé, corte do pulo entre 0 e 1 (D26).

**Arquivos:** `src/cupeco/dominio/comandos.py`, `src/cupeco/dominio/jogador.py`, `src/cupeco/conteudo/jogador.toml`, `tests/test_comandos.py`, `tests/test_jogador.py` (novos), `src/cupeco/dominio/fisica.py`, `tests/test_fisica.py`, `LOG.md`.

**Motivo / observações:**
- PR 4 do plano da Fase 1 (J1, D14, D24). Testes: 69 → 99.
- Um teste revelou que, no último quadro do dash, o estado já aparecia como "no ar" embora a Dara ainda se movesse em dash; corrigido para a animação não adiantar um quadro.
- Valores iniciais (pulo de ~200 px, corrida de 420 px/s, dash de 192 px) serão ajustados com o João na arena de testes (PR 8).
- Limitação conhecida: levantar de agachada não confere teto baixo (as arenas não têm teto baixo).
- Próximo: PR 5, `feat/armas-e-projeteis`.

### 2026-10-16 13:26 — Armas e projéteis

**Feito:**
- PR #7 (movimento da Dara) mergeado com o CI verde.
- `dominio/projeteis.py`: `Projetil` (centro, tamanho, velocidade, dano, tempo de vida, dono, material, perfura, EX), que anda em linha reta e some ao fim da vida ou fora da área; vetores das 8 direções escritos à mão (D23); caixa do projétil que acompanha a direção do voo.
- `dominio/armas.py` + `conteudo/armas.toml`: **Rajada de Plástico** (vermelho; tiro reto e rápido, 7,5 por segundo) e **Leque de Papel** (azul; 3 tiros curtos abrindo 15°), cada uma com seu tiro EX (Garrafa Perfurante, que atravessa os alvos, e Bola de Papelão). O espalhamento é dado como rotações [cosseno, seno] nos dados, sem trigonometria no jogo. Validação: arma só de material reciclável, valores positivos e rotações de tamanho 1.
- `Arsenal`: as duas armas equipadas, a ativa (a "lixeira ativa" da Triagem, D12), a troca e a cadência com o tiro segurado.
- A Dara atira com o tiro segurado, da boca do canhão na direção da mira, troca de arma com um toque e não atira nem troca durante o dash. Novos eventos `TIROU` e `TROCOU_ARMA`.
- O leitor de dados passa a converter enumerações pelo valor (ex.: `material = "papel"`), com erro que lista os valores aceitos.

**Arquivos:** `src/cupeco/dominio/projeteis.py`, `src/cupeco/dominio/armas.py`, `src/cupeco/conteudo/armas.toml`, `tests/test_armas.py` (novos), `src/cupeco/dominio/dados.py`, `src/cupeco/dominio/jogador.py`, `src/cupeco/conteudo/jogador.toml`, `tests/test_dados.py`, `tests/test_jogador.py`, `LOG.md`.

**Motivo / observações:**
- PR 5 do plano da Fase 1 (J2). Testes: 99 → 124.
- O custo do tiro EX no Medidor e o botão de EX entram no PR 6 (Triagem e Medidor); aqui só a criação do projétil EX.
- Valores iniciais de dano, cadência e alcance serão ajustados com o João na arena de testes (PR 8).
- Próximo: PR 6, `feat/triagem-e-medidor`.

### 2026-10-16 14:11 — Triagem, Medidor de Reciclagem, dano e vida

**Feito:**
- PR #8 (armas e projéteis) mergeado com o CI verde.
- `dominio/triagem.py` + `conteudo/triagem.toml`: a tabela 5.2 inteira. Resíduo reciclável da cor da arma ativa: +1 fardo (100 pontos) e separa; reciclável de outra cor: +½ fardo (50) e separa; rejeito e perigoso: não separa e causa dano (D12).
- `dominio/medidor.py`: Medidor de Reciclagem com 5 fardos de 100 pontos inteiros (D25); o EX gasta um fardo e o Super exige e gasta o Medidor cheio.
- A Dara ganha:
  - **Triagem**: apertar pulo de novo no ar abre uma janela de 10 quadros; uma tentativa por pulo; acertar quica para cima e devolve a tentativa e o dash aéreo, para encadear. O mesmo aperto continua guardado como pulo, se ela pousar logo em seguida.
  - **Vida e dano** (J5): 3 de vida, sem cura; ao levar dano, fica 18 quadros atordoada (sem controle), é empurrada para cima e para trás e fica 90 quadros invencível. Com 0 de vida, é derrotada e para de responder aos comandos. O dash continua sem invencibilidade (D14).
  - **EX e Super** (J4): o botão de EX dispara o tiro EX da arma ativa gastando um fardo; com o Medidor cheio, solta o Super (a Prensa), em que ela fica parada e invencível por 60 quadros.
  - Tiros normais que acertam enchem o Medidor (2 pontos por dano); o EX não enche.
  - Estatísticas da luta (triagens certas, de outra cor e proibidas, danos, EX e Super) para a nota (J14).
- A batalha (PR 7) vai chamar `tocar` (projétil inimigo), `tocar_perigo` (corpo do chefe) e `acertou` (tiro da Dara num alvo).

**Arquivos:** `src/cupeco/dominio/medidor.py`, `src/cupeco/dominio/triagem.py`, `src/cupeco/conteudo/triagem.toml`, `tests/test_medidor.py`, `tests/test_triagem.py`, `tests/test_jogador_combate.py` (novos), `src/cupeco/dominio/jogador.py`, `src/cupeco/conteudo/jogador.toml`, `LOG.md`.

**Motivo / observações:**
- PR 6 do plano da Fase 1 (J3, J4, J5, D12, D14, D25). Testes: 124 → 168 (inclui a matriz completa da Triagem: 6 resíduos × 2 armas).
- O `jogador.py` foi reescrito inteiro para acomodar atordoamento, Super e derrota no fluxo do passo; os 124 testes anteriores passaram sem mudança antes dos novos entrarem.
- Decisão de jogo tomada no código e registrada aqui: apertar pulo no ar abre a Triagem **e** guarda o pulo para o pouso (sem isso, tentar a Triagem perto do chão "comeria" o pulo).
- O dano do Super no chefe é aplicado pela batalha (PR 7), usando `dano_super` do `triagem.toml`.
- Próximo: PR 7, `feat/batalha-e-replay`.

### 2026-10-16 14:15 — Batalha, arena de testes em dados e replay

**Feito:**
- PR #9 (Triagem, Medidor, dano e vida) mergeado com o CI verde.
- `conteudo/arenas.toml`: a arena de testes (chão, paredes, duas tábuas atravessáveis, ponto de início, boneco de treino e lançador de resíduos), lida com validação estrita (D26).
- `dominio/batalha.py`:
  - `Batalha(semente)`: a cada passo de 1/60 s, atualiza a Dara, junta os tiros dela, aplica o Super, faz o lançador atirar, move os projéteis, resolve as colisões (tiro × boneco, projétil inimigo × Dara, com Triagem) e descarta o que morreu ou saiu da tela. Devolve os eventos do passo (os da Dara e `ACERTOU_ALVO`, `SUPER_ACERTOU`, `RESIDUO_LANCADO`).
  - Boneco de treino que soma o dano; lançador que sorteia altura e material (os 6 materiais e o ataque "sem material") com `random.Random(semente)` (D23).
  - Tiro perfurante (EX de Plástico) acerta cada alvo uma vez só, registrado no próprio projétil.
  - `Replay`: semente + botões segurados em cada passo, gravado e lido em JSON com versão; `reproduzir` roda a luta de novo (D24).
- Correção feita antes do commit: a primeira versão marcava os tiros perfurantes pelo `id()` do Python, que pode ser reaproveitado por objetos novos e quebraria a repetição exata; trocado por `alvos_atingidos` no projétil.

**Arquivos:** `src/cupeco/conteudo/arenas.toml`, `src/cupeco/dominio/batalha.py`, `tests/test_batalha.py` (novos), `src/cupeco/dominio/projeteis.py`, `LOG.md`.

**Motivo / observações:**
- PR 7 do plano da Fase 1 (D8, D23, D24). Testes: 168 → 187.
- Teste de replay: uma luta de 900 quadros com comandos aleatórios, gravada, convertida para JSON, lida de volta e reproduzida, termina no mesmo estado e com os mesmos eventos em cada passo. Outro teste roda 1200 quadros duas vezes e compara.
- Os testes do CI rodam em Linux e Windows, então a repetição é conferida nos dois sistemas.
- Próximo: PR 8, `feat/arena-de-testes` (a primeira tela jogável).

### 2026-10-16 14:24 — Arena de testes jogável

**Feito:**
- PR #10 (batalha e replay) mergeado com o CI verde.
- `ui/entrada.py`: teclado e controle (padrão Xbox, pela API GameController do SDL) viram o mesmo conjunto de botões segurados (D24, I8). Analógico com zona morta de metade do curso; gatilho direito também atira; Esc e Start pausam. Controles conectados ou desconectados durante o jogo são reconhecidos.
- `estados/arena.py`: a primeira tela jogável, com formas simples no lugar da arte: plataformas, boneco de treino com o dano somado, a Dara (pisca quando invencível; muda de cor no dano, no Super e na derrota), o canhão na direção da mira e na cor da lixeira ativa, os tiros e os resíduos.
- Leitura sem depender de cor já na arena (I4, R3): cada resíduo tem a cor da CONAMA e uma sigla; os recicláveis têm halo claro e liso, o rejeito e o perigoso têm contorno serrilhado.
- HUD: vida, os 5 fardos do Medidor (com o fardo em andamento), a arma e a lixeira ativas e a contagem de triagens.
- Avisos educativos na hora da Triagem: "Plástico na lixeira vermelha: +1 fardo!", "Vidro é da lixeira verde: só +½ fardo", "Pilha é resíduo perigoso: não se separa, vai para coleta especial!", "Rejeito não se separa: misturado ou contaminado, vai para o aterro" (D17).
- Pausa (continuar, reiniciar, sair para o título), "tentar de novo" imediato depois da derrota (I6) e F1 para mostrar as caixas de colisão, o estado da Dara, o quadro e o FPS.
- O `Jogo` passa a ter a entrada compartilhada; o título leva à arena com Enter (ou Z, ou A); `--arena` e `--semente N` no `python -m cupeco`.
- A Dara guarda o material do último resíduo que encostou nela (`ultimo_residuo`), para a interface explicar a Triagem.
- README com a situação da Fase 1 e a tabela de controles.

**Arquivos:** `src/cupeco/ui/entrada.py`, `src/cupeco/estados/arena.py`, `tests/test_arena.py` (novos), `src/cupeco/jogo.py`, `src/cupeco/estados/titulo.py`, `src/cupeco/__main__.py`, `src/cupeco/dominio/jogador.py`, `README.md`, `LOG.md`.

**Motivo / observações:**
- PR 8 do plano da Fase 1 (J7, I8, I4, I6). Testes: 187 → 204 (teclado e controle com objetos falsos, analógico na zona morta, pausa por Esc e Start, título → arena, tiros no boneco, pausa que congela, reiniciar, sair, F1, derrota e "tentar de novo", os quatro avisos da Triagem e `--arena`).
- Conferido pelo Claude numa captura da arena no meio de uma luta; corrigido o texto de ajuda que ficava ilegível sobre o chão escuro.
- **Testado à mão pelo João**: jogou a arena e aprovou ("está bom"); os valores iniciais de movimento, tiro e Triagem ficam como estão por ora.
- Não conferido: o controle de videogame com um aparelho real (testado só com controle simulado).
- Próximo: PR 9, `docs/log-fase-1` (✅ na Fase 1).

### 2026-10-16 14:27 — Fase 1 concluída

**Feito:**
- PR #11 (arena de testes jogável) mergeado com o CI verde.
- Fase 1 marcada com ✅ no roteiro do briefing; cada item do plano da seção 10.1 com ✅ e o número do PR; situação atualizada no briefing e no README (próxima: Fase 2).

**Arquivos:** `briefing.md`, `README.md`, `LOG.md`.

**Motivo / observações:**
- Fecha a Fase 1 (Regra 2). Testes: 204 → 204 (só documentação).
- Resumo da Fase 1, em 9 PRs (#3 a #11), todos com o CI verde em Linux e Windows antes do merge:
  - prancha de estilo gerada por código e aprovada pelo João (D19);
  - dados de jogo em TOML com validação estrita e os materiais da CONAMA com fonte conferida (D15, D26);
  - física com colisão por varredura e plataformas atravessáveis;
  - Dara: movimento, dash sem invencibilidade, mira em 8 direções, duas armas com EX, Triagem pela tabela 5.2, Medidor em pontos inteiros, Super, vida, dano e derrota (J1 a J5, D12, D14, D25);
  - batalha determinística com replay em JSON (D8, D23, D24);
  - arena de testes jogável com avisos educativos da Triagem, testada e aprovada pelo João (J7, I8).
- Testes ao longo da fase: 10 → 204.
- Critério do roteiro com uma ressalva: a arena funciona no teclado (testado pelo João) e no controle (testado com controle simulado); falta conferir com um controle de videogame real.
- Pendências que seguem: prazo do projeto (P4); fonte do jogo com acentos (I12, Fase 3); conferência pixel a pixel dos assets entre sistemas (R10, Fase 3).
- Próximo: Fase 2 — a primeira luta (Dom Obsolescêncio) com formas simples, padrões de ataque em dados, Modo Simples, tela de derrota com progresso e "Você sabia?", tela de vitória com nota. O plano da Fase 2 vem antes do código (Regra 1).

### 2026-10-16 14:32 — Plano da Fase 2

**Feito:**
- PR #12 (fechamento da Fase 1) mergeado com o CI verde.
- Plano da Fase 2 aprovado pelo João e registrado no briefing (seção 10.2): 9 PRs, do chefe genérico às telas da luta contra o Dom Obsolescêncio.
- Novas decisões: chefe com fases por limite de vida (D28), ataques montados com peças nos dados (D29), aviso mínimo testado em todo ataque (D30), Modo Simples como multiplicadores (D31) e nota como função pura (D32).
- Decisões de jogo do João: a vida do chefe **não** aparece na tela durante a luta (D33); os celulares da fase 2 são **destrutíveis** (D34); os fatos do "Você sabia?" vêm **do João ou do grupo**, com as fontes, e o jogo exige fonte por teste (D35).
- Situação do briefing atualizada: Fase 2 em andamento.

**Arquivos:** `briefing.md`, `LOG.md`.

**Motivo / observações:**
- Regra 1 aplicada à Fase 2: o plano vem antes do código. Testes: 204 → 204 (só documentação).
- Enquanto os fatos não chegarem, o "Você sabia?" mostra só mensagens neutras, sem afirmações sobre o mundo real (D35, C1).
- Próximo: PR 1, `feat/chefe-e-fases`.

### 2026-10-16 14:38 — Chefe genérico com fases e batalha contra chefe

**Feito:**
- PR #13 (plano da Fase 2) mergeado com o CI verde.
- `dominio/chefe.py`: `DadosChefe` e `DadosFase` (nome, porcentagem da vida em que a fase começa, tamanho, rota e velocidade), com validação; `Chefe` com vida em pontos inteiros, fase atual, transição invulnerável ao trocar de fase, movimento por rota em velocidade constante, `progresso` e `marcos` para a barra da tela de derrota (I6), e `carregar_chefe` para os arquivos de `conteudo/chefes/` (D28).
- **Nenhuma fase é pulada**: um dano grande (o Super, por exemplo) para no limite da fase seguinte e abre a transição, para todo jogador ver as 3 fases (no espírito da D13).
- Batalha generalizada: lista de alvos (boneco e/ou chefe); chefe em transição absorve os tiros sem levar dano nem encher o Medidor; dano por contato com o chefe; o Super fere todos os alvos vulneráveis; `resultado` (vitória ou derrota); arenas podem não ter boneco nem lançador.
- Replay guarda o nome do chefe (campo opcional no JSON, compatível com os replays antigos).
- O leitor de dados passa a aceitar campos opcionais (`X | None`).

**Arquivos:** `src/cupeco/dominio/chefe.py`, `tests/test_chefe.py` (novos), `src/cupeco/dominio/batalha.py`, `src/cupeco/dominio/dados.py`, `tests/test_dados.py`, `LOG.md`.

**Motivo / observações:**
- PR 1 do plano da Fase 2 (D28). Testes: 204 → 229.
- Um teste revelou que o chefe "gastava" o primeiro passo chegando ao ponto onde já estava; corrigido para começar rumo ao segundo ponto da rota.
- Sem mudança visível no jogo: o chefe aparece na tela no PR 7 da Fase 2. A arena de testes continua igual.
- Próximo: PR 2, `feat/padroes-de-ataque`.
