# Briefing — Triagem (codinome CupEco) V1

Diagnóstico, decisões e roteiro da primeira versão. Este documento vem antes do código (Regra 1) e é atualizado quando uma decisão muda; cada mudança é registrada no [LOG.md](LOG.md).

> **Situação:** concepção de game design fechada em 2026-10-16. Briefing revisado pelo João no mesmo dia, com as perguntas P1 a P6 respondidas (seção 8; só o prazo, P4, segue em aberto). Fase 0 (fundação) concluída em 2026-10-16 (PR #1). Fase 1 (núcleo e prancha de estilo) concluída em 2026-10-16 (PRs #3 a #11), com o plano da seção 10.1 e as decisões D23 a D27; pendente só conferir um controle de videogame real na arena. Fase 2 (primeira luta, Dom Obsolescêncio com formas simples) concluída em 2026-10-16 (PRs #13 a #20), com o plano da seção 10.2 e as decisões D28 a D36; o "Você sabia?" mostra só dicas do jogo até o João ou o grupo enviarem os fatos com fonte (D35).

---

## 1. Visão geral

**O que é:** **Triagem** (codinome do repositório e do pacote: CupEco, D20) é um jogo 2D de ação no estilo *run-and-gun* com foco em batalhas contra chefões (*boss rush*), inspirado na dificuldade e no ritmo de Cuphead, para conscientizar sobre reciclagem, resíduos e meio ambiente. A ambientação é **contemporânea e distópica**: **Aterrópolis**, uma megacidade brasileira fictícia de hoje em que a coleta de lixo parou (D21).

**Como ensina:** pela própria mecânica. O parry do jogo, a **Triagem**, só funciona quando o jogador separa os resíduos pela cor certa da coleta seletiva (resolução CONAMA 275/2001), e o rejeito e os resíduos perigosos não podem ser "separados" de jeito nenhum. Cada chefe representa um problema ambiental real (lixo eletrônico, poluição industrial, plástico nos oceanos). Os textos curtos ficam nos intervalos: a tela de derrota e a de vitória mostram um **"Você sabia?"** com fonte, e o **Caderno da Cooperativa** reúne o que foi desbloqueado.

**O que ele não é:** um sermão. O jogo não culpa o jogador, não aponta pessoas, empresas ou governos reais como vilões e não vende a ideia de que "reciclar resolve tudo": a mensagem final segue a ordem de prioridade da Política Nacional de Resíduos Sólidos (não gerar, reduzir, reutilizar e só então reciclar) (C2).

**Objetivo da V1:** uma campanha curta e bem acabada (1 fase de corrida e 3 chefes, de 1 a 3 horas conforme a habilidade), com a primeira luta servindo de demonstração para as ações do projeto de extensão.

**Público:** pessoas de **10 anos ou mais** (ensino fundamental II, ensino médio, universitários e comunidade das ações de extensão da UNIP). O **Modo Simples** garante que quem nunca jogou um jogo difícil chegue ao fim e veja todo o conteúdo (D13).

### 1.1 Método (os 10 princípios do projeto)

1. **Planejar antes de programar.** Este briefing vem antes do primeiro código.
2. **Cada fase deixa o projeto funcionando.** Nada de "metade pronto" na `main`.
3. **Regras separadas da interface.** A lógica fica em `dominio/`, sem pygame, e é testada sem abrir janela.
4. **Tudo que é gerado tem gerador (D10).** Personagens, cenários, efeitos de tela, sons e trilha saem de scripts versionados em `ferramentas/`, nunca de edição manual de binários. A arte é criada pelo Claude como código (P1), então a regra vale na íntegra.
5. **Diário de bordo obrigatório.** Toda mudança ganha uma entrada no `LOG.md` com o quê, o porquê e os arquivos.
6. **Histórico fino.** Um commit por arquivo, com mensagens padronizadas, e um Pull Request por mudança.
7. **A `main` é protegida.** Só entra código por PR com o CI verde.
8. **Publicar é automático e conferido.** A tag dispara o build; depois, o arquivo publicado é baixado e testado de novo.
9. **Testar de verdade antes de fechar.** Teste automático não substitui abrir o jogo. Quem pediu testa antes do commit.
10. **Experimentos podem voltar atrás.** Uma ideia testada e rejeitada sai por um PR próprio, e o LOG registra a tentativa e a volta.

---

## 2. Ponto de partida e riscos

O projeto começa do zero: o repositório [Joaofernandes-DEV/CupEco](https://github.com/Joaofernandes-DEV/CupEco) existe, é público e está vazio. Não há código anterior nem bugs a corrigir; por isso o diagnóstico lista os **riscos** que o projeto precisa controlar desde o início. Cite os códigos no LOG e nos PRs quando uma mudança tratar de um deles.

| Código | Risco | Como controlar |
|--------|-------|----------------|
| R1 | **Arte por código não chegar ao estilo esperado** ou virar o gargalo do projeto | Prancha de estilo aprovada pelo João já na Fase 1, antes de qualquer animação (D19); jogo inteiro jogável primeiro com formas simples (Fases 1 e 2); animação a 12 quadros por segundo; lista fechada de animações (seção 4); escopo da seção 9 |
| R2 | **Semelhança excessiva com Cuphead** (personagens, sprites, cenários, nome) | Só o gênero visual *rubber hose* dos anos 1930 é usado; personagens, cenários, interface e sons são originais; nada de Cuphead entra no repositório, nem como referência (D11); título próprio, "Triagem" (D20) |
| R3 | **Daltonismo:** a Triagem depende de cores (vermelho e verde, por exemplo) | Todo resíduo tem cor **e** ícone **e** silhueta próprios (I4, D15); teste que exige ícone para cada material |
| R4 | **Fotossensibilidade:** explosões, flashes e tremor de tela | No máximo 3 flashes por segundo; opções para reduzir tremor, flashes e grão de filme (I9) |
| R5 | Dificuldade **afastar o público** da extensão | Modo Simples com as 3 fases de cada chefe (D13); todo ataque com aviso mínimo testado (J6); "tentar de novo" em menos de 1 segundo (I6) |
| R6 | Informação ambiental **errada ou sem fonte** | Todo fato tem fonte registrada nos dados (C1); teste que exige fonte; revisão externa (D22) |
| R7 | Vilões associados a **pessoas, empresas, marcas ou governos reais**; catadores retratados com desprezo | Chefes são "Rejeitos", criaturas do descarte, sem logotipos nem marcas reais (C3); catadores com dignidade e protagonismo (C4) |
| R8 | **Mensagem simplista** ("é só reciclar") ou catastrofista, que paralisa | Hierarquia da PNRS na história e nos fatos (C2); tom de esperança e ação (C5) |
| R9 | **Desempenho** do pygame com arte em alta resolução em computadores de escola | Resolução lógica de 1280×720 (D4); atlas com `convert_alpha`; limite de projéteis e partículas por tela; FPS medido em todas as lutas; meta de 60 FPS (seção 7) |
| R10 | **Assets gerados fora de sincronia** com os geradores (alguém muda o script e esquece de regenerar) ou repositório pesado | Geradores determinísticos com Pillow em versão fixa; o CI regenera tudo e falha se algum arquivo mudar; tamanho do repositório acompanhado no LOG (D10) |
| R11 | Fonte de estilo anos 30 **sem acentos** do português | Escolher uma fonte de licença OFL e conferir todos os acentos antes de adotá-la (I12) |
| R12 | Áudio gerado por código **soar fora do estilo** (chiptune em vez de big band) | Trilha em estilo ragtime com síntese de piano, metais e bateria, ouvida e aprovada pelo João antes de entrar (P2) |
| R13 | A pasta de usuário (`C:\Users\joaov`) também é um repositório git, e um commit pode cair no lugar errado | Conferir `git rev-parse --show-toplevel` antes de commitar; a Fase 0 transforma `CupEco/` num repositório próprio (D1) |

---

## 3. Estrutura do código

```plaintext
CupEco/
├── CLAUDE.md, CONTRIBUTING.md, README.md, LOG.md, briefing.md
├── LICENSE (MIT, código), LICENCA-CONTEUDO.md (CC BY 4.0, arte, sons e textos)
├── pyproject.toml
├── .github/workflows/ci.yml          # release.yml entra na Fase 8
├── src/cupeco/
│   ├── __main__.py                   # python -m cupeco [--fechar-em S] [--luta ID] [--modo simples]
│   ├── config.py                     # resolução, FPS, caminhos
│   ├── jogo.py                       # janela, loop de passo fixo e pilha de estados
│   ├── persistencia.py               # save JSON e autosave
│   ├── dominio/                      # regras puras, sem pygame
│   │   ├── fisica.py                 # gravidade, caixas de colisão, plataformas
│   │   ├── comandos.py               # o que o jogador apertou neste quadro
│   │   ├── jogador.py                # máquina de estados da Dara (e do voo com o Pet)
│   │   ├── materiais.py              # cores CONAMA, ícones, reciclável/rejeito/perigoso
│   │   ├── armas.py, projeteis.py    # armas, tiros, EX e Super
│   │   ├── triagem.py                # regras do parry (D12)
│   │   ├── medidor.py                # Medidor de Reciclagem (fardos)
│   │   ├── padroes.py                # padrões de ataque em dados, com aviso
│   │   ├── chefe.py                  # fases por limiar de vida e transições
│   │   ├── batalha.py                # uma luta: atualizar(comandos) → eventos
│   │   ├── corrida.py                # fase run-and-gun: rolagem, inimigos, selos
│   │   ├── modos.py                  # Normal e Simples
│   │   ├── nota.py                   # nota da luta (tempo, vida, triagens, super)
│   │   ├── progresso.py              # chefes vencidos, notas, fatos desbloqueados
│   │   └── fatos.py                  # "Você sabia?" e Caderno
│   ├── conteudo/                     # dados revisáveis (TOML)
│   │   ├── chefes/*.toml             # vida, fases, padrões, velocidades
│   │   ├── armas.toml, modos.toml
│   │   └── pt_BR/textos.toml, fatos.toml
│   ├── estados/                      # telas: título, mapa, luta, corrida, resultado, caderno…
│   ├── ui/                           # animador, câmera, HUD, efeito de filme, texto
│   └── assets/                       # GERADOS por ferramentas/ (nunca editar à mão)
├── ferramentas/
│   ├── arte/                         # a arte como código (D10)
│   │   ├── traco.py                  # Bézier, "mangueira", olhos pie-cut, linha viva
│   │   ├── personagens/*.py          # Dara, Pet, chefes: formas, rig e poses
│   │   └── cenarios/*.py
│   ├── gerar_sprites.py              # personagens → assets/sprites/*.png + .json
│   ├── gerar_efeitos.py              # grão, vinheta, aviso de ataque…
│   ├── gerar_sons.py, gerar_trilha.py
│   └── empacotar.py                  # executável + teste de fumaça
├── docs/                             # roteiro da história, GIF e notas de release
└── tests/
```

**Decisões técnicas:**

- **Python 3.11+ e pygame-ce** (D4): o método já foi testado no Jogo da Cobrinha e no Politicalizando, roda no CI sem janela e permite testar regras sem interface (Regra 3).
- **Resolução lógica de 1280×720** com `pygame.SCALED`: o traço de desenho animado não é pixel art e precisa de mais resolução; o tamanho da janela se ajusta à tela.
- **Passo fixo de 60 Hz e simulação determinística** (D8): o domínio avança sempre 1/60 s por chamada e usa números aleatórios com semente por luta. Assim uma luta inteira pode ser **reproduzida** a partir de uma lista de comandos, o que permite testes de replay e repetir bugs.
- **Domínio sem pygame:** `tests/test_dominio.py` impede que o pygame entre em `dominio/`. A interface só lê o estado e os **eventos** produzidos pela batalha (`Acertou`, `Triagem`, `TriagemErrada`, `TomouDano`, `MudouFase`, `Venceu`, `Morreu`) para tocar sons, animações e efeitos.
- **Ataques em dados:** vida, fases, padrões, velocidades e avisos de cada chefe ficam em TOML, para balancear sem mexer no código e para testar regras de justiça (todo ataque tem aviso mínimo, J6).
- **Arte como código** (D10): cada personagem é descrito em Python como formas vetoriais (curvas de Bézier, membros de "mangueira", olhos *pie-cut*) presas a um esqueleto simples de poses. O gerador desenha cada quadro com o Pillow em resolução 4× maior e reduz (antialiasing), aplica uma leve variação de traço por quadro com semente fixa (a "linha viva" que imita o desenho à mão) e monta o spritesheet com um JSON de quadros, durações, ponto de âncora e caixas de colisão. O Pillow fica numa versão fixa para o resultado ser idêntico em qualquer máquina, e o CI confere que os assets estão em dia.
- **Formas simples antes da arte:** até a Fase 3, tudo é desenhado com retângulos e círculos coloridos. O jogo é jogável e testável antes de existir qualquer arte final (R1).

---

## 4. Interface

| Código | Item |
|--------|------|
| I1 | **Rubber hose original, gerado por código:** membros de "mangueira", olhos *pie-cut*, contorno grosso com "linha viva", cor aguada e animação elástica a 12 quadros por segundo. Diferenças de propósito: a Dara usa **luvas de trabalho amarelas** (não as luvas brancas clássicas), e o Pet é um robô de corpo de lata com tronco de garrafa, **sem cabeça de objeto** (R2) |
| I2 | **Efeito de filme** gerado por código: grão, vinheta, cor levemente desbotada e riscos ocasionais. Pode ser desligado (I9) |
| I3 | **HUD:** vida (3 pontos), Medidor de Reciclagem com 5 fardos, arma ativa com cor e ícone do material |
| I4 | **Leitura da Triagem:** todo resíduo tem cor CONAMA + ícone + silhueta (papel = folha amassada, plástico = garrafa, vidro = pote, metal = lata). Rejeito (cinza) e perigoso (laranja) têm contorno serrilhado e símbolo de proibido/perigo (R3, D15) |
| I5 | **Aviso de ataque:** todo ataque tem um aviso visual e sonoro antes de acontecer (J6) |
| I6 | **Tela de derrota:** barra de progresso da luta com os marcos de fase, um "Você sabia?" e **tentar de novo em menos de 1 segundo** |
| I7 | **Tela de vitória:** nota, estatísticas (tempo, vida, triagens certas, supers) e um fato |
| I8 | **Controles:** teclado e controle de videogame (D9). Os botões mostrados na tela mudam conforme o dispositivo em uso. Teclado padrão: setas movem, **Z** pula/Triagem, **X** atira, **C** dash, **V** tiro EX, **Shift** trava a posição para mirar, **Tab** troca de arma, **Esc** pausa |
| I9 | **Acessibilidade:** reduzir tremor de tela; reduzir flashes (no máximo 3 por segundo em qualquer caso); desligar o grão; falas sempre em texto; nenhuma informação só por cor |
| I10 | **Menus:** título (novo jogo, continuar), mapa da cidade, opções, Caderno da Cooperativa, créditos e fontes, sair |
| I11 | **Som:** efeitos e trilha em estilo ragtime/big band dos anos 30, tudo gerado por script (P2) |
| I12 | **Fonte** de licença OFL com cara de anos 30 e todos os acentos do português conferidos (R11) |
| I13 | **História em quadrinhos:** abertura (6 a 8 quadros), uma fala de cada chefe antes da luta e um final (4 quadros), no formato de um gibi da cooperativa |

**Lista fechada de animações da V1** (R1): Dara com parada, corrida, pulo, queda, dash, Triagem, tiro em 8 direções, dano, derrota e vitória; Pet-planador (voo) com parado, tiro, dano; cada chefe com 3 conjuntos (um por fase) de parado, ataque e transição, mais a derrota. Qualquer animação nova entra no briefing antes de ser criada.

---

## 5. Funcionalidades

**Premissa narrativa:** em Aterrópolis, uma megacidade brasileira fictícia de hoje (D21), a coleta parou: contratos vencidos, cooperativas fechadas, lixo acumulando por meses. Do fundo do aterro, os resíduos misturados se fundem e ganham vida: são os **Rejeitos**. **Dara**, catadora de 16 anos da última cooperativa aberta, transforma uma máquina de triagem num canhão e, com o robô **Pet**, atravessa a cidade para derrotar os três maiores Rejeitos e devolver cada núcleo à cooperativa, onde ele pode ser separado e reaproveitado. Mas a cada vitória a cooperativa enche de novo, e o final mostra que reciclar é o último recurso: antes vêm **repensar, recusar e reduzir** (C2).

### 5.1 Jogador e combate

| Código | Funcionalidade |
|--------|----------------|
| J1 | **Movimento:** correr, pular com altura variável, agachar, dash (1 no ar), mirar em 8 direções e travar a posição para mirar |
| J2 | **Armas da V1 (as duas equipadas, troca com uma tecla):** **Plástico** (vermelho): rajada reta e rápida, dano baixo por tiro e alcance longo. **Papel** (azul): leque de 3 tiros curtos, dano alto de perto. Cada uma tem um tiro EX |
| J3 | **Triagem (parry):** no ar, apertar pulo de novo encostando num resíduo colorido. A regra está na tabela 5.2 |
| J4 | **Medidor de Reciclagem:** 5 fardos. Enche com o dano causado e com triagens. 1 fardo = tiro EX; 5 fardos = Super **Prensa** (uma prensa de reciclagem cai sobre o chefe) |
| J5 | **Vida:** 3 pontos, sem cura. Após um dano, a Dara fica invencível por um instante. **O dash não dá invencibilidade** (D14) |
| J6 | **Justiça dos ataques:** todo ataque tem aviso mínimo (Normal: 20 quadros; Simples: 30 quadros), conferido por teste nos dados |
| J7 | **Pausa** a qualquer momento, com reiniciar luta e voltar ao mapa |

### 5.2 Triagem híbrida (D12)

A "lixeira ativa" é a **cor da arma equipada**; não existe botão extra.

| Resíduo tocado | Arma ativa da mesma cor | Arma ativa de outra cor |
|----------------|-------------------------|-------------------------|
| Reciclável (azul, vermelho, verde ou amarelo) | **+1 fardo** inteiro e o resíduo é "separado" (some com efeito) | **+½ fardo** e o resíduo é separado |
| Rejeito (cinza) | não pode ser separado: **dano** | **dano** |
| Perigoso (laranja: pilhas, baterias) | não pode ser separado: **dano** | **dano** |

Verde (vidro) e amarelo (metal) aparecem nos ataques mesmo sem as armas de vidro e de metal na V1: rendem sempre meio fardo e mantêm as 4 cores principais no jogo. As estatísticas contam **triagens certas**, **triagens de outra cor** e **triagens proibidas** (tentativas em cinza ou laranja).

### 5.3 Chefes

Cada chefe tem **3 fases por limiar de vida**. Na troca de fase há uma animação de transição em que o chefe fica invulnerável por pouco tempo, e a arena pode mudar.

| Código | Chefe | Fase 1 | Fase 2 | Fase 3 |
|--------|-------|--------|--------|--------|
| J8 | **Dom Obsolescêncio** (lixo eletrônico; tema: obsolescência programada) | **Torre de Tubos:** pilha de TVs de tubo com raios de pixel, chicotes de cabo e uma coroa de antenas de metal que cai em pedaços amarelos (metal, separáveis; D36) | **Enxame Descontinuado:** celulares voadores; **baterias estufadas** (laranja, não separáveis) explodem em área | **Placa-Mãe:** chão com trilhas elétricas; a barra de "Atualização Obrigatória" cura o chefe se encher e precisa ser destruída a tiros |
| J9 | **Barão Fuligem** (poluição industrial do ar e da água) | **Linha de Produção:** esteiras no chão e chaminés soltando nuvens de fuligem em ritmo | **Descarga no Rio:** luta sobre balsas num rio com espuma química (referência: a espuma do rio Tietê em Pirapora do Bom Jesus); plataformas afundam | **Fornalha:** smog limita a visão a um círculo em volta da Dara; o ponto fraco só aparece quando a fornalha "respira" |
| J10 | **Leviatã de Plástico** (plástico nos oceanos) | **Ilha de Sacolas:** sacolas-água-viva em ondas e chuva de tampinhas | **Serpente de Redes-Fantasma:** fase de **voo**; o Pet vira um planador de garrafa PET, e a Dara voa e atira em 8 direções | **Microplástico:** o chefe se dissolve num enxame minúsculo e espalhado, difícil de acertar |

### 5.4 Campanha e conteúdo

| Código | Funcionalidade |
|--------|----------------|
| J11 | **Fase de corrida "Feirão Eletrônico":** rolagem lateral de 2 a 3 minutos com inimigos (ratos de computador com cauda de cabo, carregadores-cobra, impressoras que cospem folhas azuis separáveis) e **5 Selos Verdes** escondidos |
| J12 | **Mapa da cidade:** tela fixa com 3 regiões (Feirão Eletrônico, Distrito Industrial, Orla). Ordem da V1: Feirão → Dom Obsolescêncio → Barão Fuligem → Leviatã de Plástico |
| J13 | **Modos Normal e Simples** (D13). Valores iniciais do Simples, ajustados no balanceamento: chefe com −30% de vida, −30% de projéteis, velocidade −20% e avisos +50%. As 3 fases de cada chefe continuam no Simples |
| J14 | **Nota da luta** (A+ a D) por tempo, vida restante, triagens certas e uso do Super. O modo fica registrado ao lado da nota |
| J15 | **"Você sabia?":** na derrota e na vitória, um fato curto, com fonte, ligado ao chefe da luta; sorteio sem repetição até esgotar os fatos daquele chefe |
| J16 | **Caderno da Cooperativa:** guarda os fatos já vistos, a tabela de cores CONAMA e as fontes. Cada Selo Verde desbloqueia uma ficha extra |
| J17 | **História:** abertura, fala de cada chefe antes da luta e final, em quadrinhos (I13) |
| J18 | **Save** em JSON, 1 slot, com autosave depois de cada luta e de cada fase de corrida (D18) |

---

## 6. Princípios de conteúdo

Valem para todo texto, fato, imagem, som e mecânica, e são conferidos na revisão de cada PR de conteúdo.

| Código | Princípio |
|--------|-----------|
| C1 | **Todo fato tem fonte.** As fontes são buscadas pela Consensus e por pesquisa própria, com preferência por material em português e por fontes confiáveis (órgãos oficiais, legislação, artigos revisados por pares, instituições de pesquisa); **nunca livros**. A fonte fica registrada junto do fato nos dados |
| C2 | **Reciclar é o último R, não o primeiro.** A ordem da PNRS (Lei 12.305/2010): não geração, redução, reutilização, reciclagem, tratamento e disposição final. O jogo nunca sugere que reciclar compensa consumir sem pensar |
| C3 | **Nenhum vilão real.** Os chefes são criaturas do descarte. Sem marcas, logotipos, empresas, pessoas ou governos reais, nem alusões a eles |
| C4 | **Catadores com dignidade.** A protagonista é catadora; a profissão aparece como trabalho essencial e qualificado, reconhecido pela PNRS, nunca como motivo de pena ou piada |
| C5 | **Esperança e ação, não culpa.** O jogo não culpa o jogador nem paralisa com catástrofe: todo problema mostrado vem acompanhado de algo que se pode fazer |
| C6 | **Precisão sobre a coleta.** As cores seguem a CONAMA 275/2001, e os fatos explicam que muitas cidades usam a coleta em duas frações (seco e úmido), para o jogador não achar que "faz errado" em casa |
| C7 | **Texto curto.** No máximo 2 frases por fato na tela; o aprofundamento fica no Caderno |
| C8 | **Humor sem alvo frágil.** O humor vem do absurdo dos Rejeitos (a "Atualização Obrigatória", o Barão de cartola de chaminé), nunca de pessoas, profissões ou grupos sociais |

---

## 7. Desempenho, qualidade e entrega

- **Desempenho:** 60 FPS estáveis em computadores modestos de escola em todas as lutas, medidos e registrados no LOG; o jogo abre em poucos segundos; "tentar de novo" em menos de 1 segundo.
- **Testes:** `pytest`. Regras do domínio testadas sem janela; telas testadas com o driver `dummy` do SDL. Testes específicos:
  - **matriz da Triagem** (tabela 5.2 inteira);
  - **replay:** uma lista de comandos gravada reproduz a mesma luta, quadro a quadro;
  - **troca de fase** nos limiares de vida e invulnerabilidade na transição;
  - **justiça dos ataques:** todo padrão tem aviso mínimo nos dois modos (J6);
  - **conteúdo:** todo fato tem fonte, todo ID de texto existe, todo material tem cor e ícone (R3);
  - **assets em dia:** rodar os geradores de `ferramentas/` não muda nenhum arquivo de `assets/` (no CI, em Ubuntu com Python 3.11).
- **Lint:** `ruff` (`line-length = 100`, regras `E, F, W, I, UP, B, SIM, N`).
- **CI:** Ubuntu 24.04 com Python 3.11, 3.12 e 3.13, mais Windows com 3.11, e `fail-fast: false`.
- **Distribuição:** executável Windows (`.exe`) gerado pelo `release.yml` a partir de uma tag `v*` e conferido depois de publicado (sha256 e teste de fumaça com `--fechar-em`).
- **Documentação:** README com GIF, CONTRIBUTING, CLAUDE.md, LOG completo e notas de cada release.

---

## 8. Decisões tomadas

| # | Pergunta | Decisão | Motivo |
|---|----------|---------|--------|
| D1 | Onde fica o clone local? | `Documents\Estudos\UNIP\ProjetoExtensao\CupEco`, transformado em repositório próprio na Fase 0 (`git init` + `origin` apontando para o GitHub, já que a pasta não está vazia) | Mesmo padrão dos outros projetos de extensão; a pasta de usuário também é um repositório git (R13) |
| D2 | Público e faixa etária? | 10 anos ou mais | Violência só cartunesca contra monstros de lixo; o Modo Simples abre o jogo para quem nunca jogou |
| D3 | Plataforma? | Windows `.exe` na V1; versão web (pygbag) fica para a próxima | Fluxo de release já testado; a web exige adaptar o loop e medir desempenho |
| D4 | Biblioteca? | Python 3.11+ e pygame-ce, resolução lógica 1280×720 com `pygame.SCALED` | Método já testado; domínio testável sem janela. Motores como Godot dificultariam a Regra 3 e o fluxo de CI já conhecido |
| D5 | Licença? | Código sob MIT; arte, sons e textos sob CC BY 4.0 | Professores e outros projetos podem reutilizar o material citando a fonte |
| D6 | Escopo da V1? | Dara solo, 2 armas, 3 chefes com 3 fases, 1 fase de corrida, Modo Simples | Concepção aprovada em 2026-10-16; entregar completo em vez de muito pela metade (R1) |
| D7 | Versão? | `0.1.0` no desenvolvimento; `1.0.0` na entrega da V1 | Versionamento semântico; a tag só é criada quando o João pedir |
| D8 | Como simular? | Passo fixo de 60 Hz, números aleatórios com semente por luta, domínio determinístico | Replays, testes reproduzíveis e bugs que podem ser repetidos |
| D9 | Controles? | Teclado e controle de videogame na V1; remapear teclas fica para a próxima | Jogos de ação pedem controle; o teclado garante que qualquer computador da escola roda |
| D10 | Como fica a Regra 4? | **Arte como código, criada pelo Claude** (P1): personagens e cenários descritos em Python (`ferramentas/arte/`), desenhados com o Pillow em versão fixa e montados em spritesheets por `ferramentas/gerar_sprites.py`; sons, trilha e efeitos de tela também gerados por script. A regra volta a valer na íntegra | Em 2026-10-16 o João tinha revisado a regra para aceitar arte à mão (`.ora` do Krita); ao decidir que o Claude cria a arte, tudo passa a sair de código. A porta para arte humana em `.ora` fica para a próxima versão (seção 9) |
| D11 | Qual estilo visual? | *Rubber hose* dos anos 1930 com personagens, cenários e interface **originais**. Cuphead é referência só de gênero e de ritmo de jogo; nenhum sprite, personagem, cenário, som ou texto dele é copiado ou guardado no repositório | Decisão do João em 2026-10-16. Uma cópia exata infringiria direitos da Studio MDHR e arriscaria a remoção do projeto (R2) |
| D12 | Como funciona o parry? | **Triagem híbrida** (tabela 5.2): a lixeira ativa é a cor da arma; cor certa = 1 fardo, outra cor reciclável = ½ fardo; cinza e laranja causam dano | Decisão do João em 2026-10-16 (variante C). Na conversa a regra foi escrita como "enche o super inteiro"; aqui virou "1 fardo inteiro", porque uma única triagem não pode liberar o Super (balanceamento) |
| D13 | Como é o Modo Simples? | Menos vida no chefe, menos projéteis, mais lentos e com mais aviso, **mantendo as 3 fases** | Diferente de Cuphead de propósito: num jogo educativo ninguém pode perder o conteúdo da fase 3 por falta de habilidade (R5) |
| D14 | O dash dá invencibilidade? | Não | Fiel ao gênero: o dash serve para posicionar, e a dificuldade vem de ler os ataques |
| D15 | Como representar os materiais? | Cores da CONAMA 275/2001 + ícone + silhueta para cada material | Conteúdo real e legível por pessoas daltônicas (R3) |
| D16 | Quem são os protagonistas? | Dara (catadora de 16 anos) e Pet (robô de sucata). Na V1 o Pet aparece na história e como planador na fase de voo do Leviatã; o co-op local fica para a próxima | Concepção aprovada em 2026-10-16; o co-op dobra o trabalho de arte e de balanceamento (R1) |
| D17 | Como o conteúdo educativo entra? | Pela mecânica (Triagem), pelos chefes, pelo "Você sabia?" nas telas de derrota e vitória e pelo Caderno; nunca interrompendo a ação | Mantém o ritmo de jogo difícil e transforma cada derrota num momento de aprender |
| D18 | Como salvar? | JSON, 1 slot, autosave depois de cada luta e de cada fase de corrida | Legível, seguro e testável; vários perfis ficam para a próxima |
| D19 | Como validar o estilo da arte por código? | Uma **prancha de estilo** (a Dara em 3 poses, um resíduo de cada material e um pedaço de cenário) é gerada na Fase 1 e aprovada pelo João antes de qualquer animação | O estilo é o maior risco da arte por código (R1); errar cedo custa pouco |
| D20 | Qual é o título do jogo? | **Triagem**. "CupEco" continua como nome do repositório e do pacote (`cupeco`) | O "Cup" lembra diretamente a marca Cuphead (R2); "Triagem" nomeia a mecânica central. Nenhum jogo com esse título foi encontrado em 2026-10-16 |
| D21 | Qual é a cidade? | **Aterrópolis**, megacidade brasileira fictícia | Nenhum lugar real com esse nome foi encontrado em 2026-10-16; o nome já conta o problema da cidade |
| D22 | Haverá revisão externa? | Sim: um professor ou professora de Biologia, Engenharia Ambiental ou Química revisa os fatos antes da Fase 7, e um grupo do público da extensão testa o jogo antes da release | Fatos corretos (R6) e dificuldade medida com o público real (R5) |
| D23 | Como garantir que a mesma luta sai igual em qualquer máquina? | O domínio usa números decimais só com as quatro operações (constantes como o seno de 15° ficam escritas no código, sem `math.sin` durante o jogo) e sorteia com `random.Random(semente)` | Resultado idêntico no Windows, no Linux do CI e em qualquer versão do Python suportada (D8) |
| D24 | Como o domínio recebe os controles? | **Comandos** = conjunto de botões segurados em cada passo; o domínio calcula quando um botão acabou de ser apertado. Um **replay** é a semente mais a lista de comandos | Teclado e controle viram a mesma coisa; replays pequenos e testes simples |
| D25 | Como contar o Medidor de Reciclagem? | Em **pontos inteiros**: 100 pontos = 1 fardo; triagem certa +100, de outra cor +50 | Sem "meio fardo" em número decimal; conta exata e testável (D12) |
| D26 | Onde ficam os valores de jogo? | Em TOML (`src/cupeco/conteudo/`), lidos com validação estrita: chave desconhecida ou faltando é erro | Equilíbrio ajustado sem mexer no código; erro de digitação não passa em silêncio |
| D27 | Como entram as ferramentas de arte? | Pillow em versão fixa no extra `[ferramentas]` do `pyproject.toml`; a prancha de estilo é gerada em `docs/prancha-estilo.png` | Arte como código reproduzível (D10, D19); o jogo em si não depende do Pillow |
| D28 | Como funciona um chefe? | Vida em pontos inteiros; troca de fase quando a vida cai abaixo de limites definidos nos dados (ex.: 66% e 33%); na transição fica invulnerável por um tempo e a arena pode mudar | Padrão do gênero e testável sem janela |
| D29 | Como se descrevem os ataques? | Por peças pequenas nos dados (rajada, leque, tiro mirado na Dara, chuva vinda do alto, zona de perigo no chão e inimigos menores); cada fase tem a sua lista de ataques, em ordem sorteada com semente (D23) | Os três chefes reaproveitam as mesmas peças; o equilíbrio é ajustado no TOML (D26) |
| D30 | Como garantir ataques justos? | Todo ataque tem aviso antes de causar dano; um teste confere, em todos os ataques, o mínimo de 20 quadros no Normal e 30 no Simples (J6) | A dificuldade vem de ler o ataque, não de ser pego de surpresa (R5) |
| D31 | Como se aplica o Modo Simples? | Um conjunto de multiplicadores aplicado ao carregar a luta: vida −30%, projéteis −30%, velocidade −20%, aviso +50%, mantendo as 3 fases (D13) | Um só lugar para ajustar a dificuldade; um teste garante que nenhuma fase some |
| D32 | Como se calcula a nota? | Função pura do tempo, da vida restante, das triagens certas e do uso do Super, com faixas nos dados; o modo fica registrado ao lado da nota (J14) | Testável e ajustável sem mexer no código |
| D33 | A vida do chefe aparece na tela? | **Não**: o avanço é percebido pelas trocas de fase, e a barra de progresso aparece na tela de derrota (I6) | Decisão do João em 2026-10-16: tensão do gênero e valor do progresso ao perder |
| D34 | Os celulares da fase 2 do Dom podem ser destruídos? | **Sim**: "inimigos menores" que voam até a Dara, machucam no contato e caem com tiros, como peça de ataque reaproveitável (D29) | Decisão do João em 2026-10-16: fase mais viva e sistema útil para os outros chefes |
| D35 | Quem traz os fatos do "Você sabia?"? | **O João ou o grupo**, com as fontes; o Claude coloca no jogo, com teste que exige fonte. Sem fato fornecido, a tela mostra só mensagens neutras, sem nenhuma afirmação sobre o mundo real. A revisão externa (D22) continua na Fase 7 | Decisão do João em 2026-10-16 (C1, R6) |
| D36 | Do que é feita a coroa do Dom (fase 1)? | De **antenas de metal**, que caem em pedaços amarelos separáveis; não de carregadores | Decisão do João em 2026-10-16. Amarelo no jogo é metal, separável; carregador é lixo eletrônico e vai para a coleta de eletrônicos, então a coroa de carregadores ensinaria a separação errada (C1, R6) |

**Perguntas respondidas na revisão de 2026-10-16:**

- **P1.** Quem cria a arte: **o Claude**, como código (D10, D19).
- **P2.** Trilha sonora **gerada por script** (I11, R12).
- **P3.** Revisão externa: **sim** (D22).
- **P5.** Cidade: **Aterrópolis** (D21).
- **P6.** Título: **Triagem**, com CupEco como codinome (D20).

**Pergunta em aberto:**

- **P4. Prazo:** qual é a data de entrega do projeto de extensão? O roteiro da seção 10 é ajustado a ela.

---

## 9. Escopo

| Entra nesta versão (V1) | Fica para a próxima |
|-------------------------|---------------------|
| Dara jogável, solo | Co-op local com o Pet (Jogador 2) |
| 2 armas: Plástico (vermelho) e Papel (azul), com EX | Armas de Vidro (verde) e Metal (amarelo); loja de armas |
| 1 Super (Prensa) | Escolha entre vários Supers; amuletos/modificadores |
| 3 chefes com 3 fases cada, incluindo a fase de voo do Leviatã | 4º chefe secreto, "O Aterro"; novos chefes (agrotóxico, esgoto, desmatamento) |
| 1 fase de corrida (Feirão Eletrônico) com 5 Selos Verdes | Fases de corrida do Distrito Industrial e da Orla |
| Mapa da cidade em tela fixa | Mapa com a Dara andando pela cidade |
| Modos Normal e Simples | Modo Expert; desafios (sem tiro, sem dano) |
| "Você sabia?" e Caderno da Cooperativa com fontes | Material de apoio para professores |
| História em quadrinhos (abertura, falas, final) | Cenas animadas e dublagem |
| Teclado e controle | Remapear teclas e controles |
| Executável Windows | Versão web (pygbag) e outras plataformas |
| Texto em português | Outros idiomas |
| Sons e trilha gerados por script | Trilha gravada com instrumentos reais |
| Arte gerada por código | Pipeline para arte desenhada à mão (`.ora` do Krita → spritesheets) |
| Save de 1 slot com autosave | Vários perfis de save e estatísticas gerais |

---

## 10. Roteiro em fases

Cada fase termina com o jogo funcionando na `main` (Regra 2). Até a Fase 2 tudo é desenhado com formas simples; a arte entra a partir da Fase 3.

| Fase | Foco | Itens | Pronto quando… |
|------|------|-------|----------------|
| 0. Fundação ✅ | Repositório, esqueleto, lint, CI, documentos | D1 a D7, R13 | O jogo abre e fecha sem erro (`--fechar-em`); lint e CI passando; `main` protegida; CLAUDE.md, CONTRIBUTING, README, LOG e licenças criados |
| 1. Núcleo ✅ | Jogador e combate no domínio; prancha de estilo | D8, D12, D14, D15, D19, J1 a J5, J7 | Física, Dara, armas, Triagem, Medidor e dano modelados e testados sem janela (matriz da Triagem e replay); uma **arena de testes** com retângulos pode ser jogada no teclado e no controle; **prancha de estilo aprovada pelo João** |
| 2. Primeira luta ✅ | Dom Obsolescêncio com formas simples | J6, J8, J13, J14, J15, D13, D17, R5 | As 3 fases do Dom podem ser jogadas do início ao fim nos dois modos, com padrões em dados, avisos testados, tela de derrota com progresso e "Você sabia?", e tela de vitória com nota |
| 3. Arte e som | Pipeline e primeira luta com arte final | D10, D11, I1 a I9, I11, I12, R2, R3, R4, R9, R11, R12 | Geradores de arte funcionando e conferidos no CI; Dara e Dom Obsolescêncio com arte final; efeito de filme, HUD, sons e trilha; 60 FPS medidos; **demonstração pronta para a extensão** |
| 4. Barão Fuligem | Segundo chefe | J9 | As 3 fases jogáveis com formas simples, depois com arte final, nos dois modos, a 60 FPS |
| 5. Leviatã de Plástico | Terceiro chefe e fase de voo | J10, D16 | O voo com o Pet-planador funciona e é testado no domínio; as 3 fases com arte final, nos dois modos, a 60 FPS |
| 6. Campanha | Mapa, corrida, história e save | J11, J12, J16, J17, J18, I10, I13 | O jogo completo pode ser jogado do título ao final, com o Feirão Eletrônico, os Selos Verdes, o Caderno, os quadrinhos e o save |
| 7. Conteúdo e polimento | Fatos, balanceamento e testes com pessoas | C1 a C8, R6, R7, R8, D22 | Todos os fatos com fonte e revisados; balanceamento dos dois modos ajustado com um grupo de teste; acessibilidade conferida; créditos completos |
| 8. Entrega | Portfólio e release | — | README com GIF, CI verde, `release.yml`, executável na release v1.0.0 conferido e LOG completo |

Marque ✅ na fase ao concluí-la e registre no LOG.

### 10.1 Plano da Fase 1 (aprovado e concluído em 2026-10-16)

Um PR por item, cada um com testes, entrada no LOG e CI verde. A prancha vem primeiro porque é o maior risco e depende da aprovação do João; enquanto ela é avaliada, os PRs 2 a 7 seguem, porque não dependem dela.

| # | Branch | Entrega | Itens |
|---|--------|---------|-------|
| 0 ✅ | `docs/plano-fase-1` (PR #3) | Este plano e as decisões D23 a D27 | — |
| 1 ✅ | `feat/prancha-de-estilo` (PR #4) | Biblioteca de traço (Bézier, membros de "mangueira", olhos *pie-cut*, "linha viva"); Dara em 3 poses, os 6 resíduos com cor, ícone e silhueta e um pedaço de cenário; aprovação do João | D19, D27, R1, I1, I4 |
| 2 ✅ | `feat/dados-e-materiais` (PR #5) | Leitor de TOML com validação; materiais da CONAMA com cor, ícone e tipo (reciclável, rejeito, perigoso); teste de que nenhum material depende só de cor | D15, D26 |
| 3 ✅ | `feat/fisica` (PR #6) | Caixas de colisão, gravidade, chão e plataformas atravessáveis por baixo, colisão resolvida eixo por eixo | — |
| 4 ✅ | `feat/jogador-movimento` (PR #7) | Comandos; Dara corre, pula com altura variável (com tolerância na beirada e pulo guardado antes de pousar), agacha, faz dash (1 no ar, sem invencibilidade), trava a posição e mira em 8 direções | J1, D14, D24 |
| 5 ✅ | `feat/armas-e-projeteis` (PR #8) | Plástico (rajada) e Papel (leque) em dados, cadência, troca de arma, projéteis com tempo de vida, tiros EX | J2 |
| 6 ✅ | `feat/triagem-e-medidor` (PR #9) | Tabela 5.2 completa; Medidor com EX e Super; vida 3, invencibilidade após dano, Dara derrotada | J3, J4, J5, D12, D25 |
| 7 ✅ | `feat/batalha-e-replay` (PR #10) | `Batalha` com passo fixo, semente e eventos; boneco de treino e lançador de resíduos de todas as cores; replay em JSON e teste de que a mesma luta repetida dá o mesmo resultado | D8, D23 |
| 8 ✅ | `feat/arena-de-testes` (PR #11) | Tela jogável com retângulos (resíduos com letra e ícone), HUD provisório, teclado e controle, pausa (continuar, reiniciar, sair) e F1 para mostrar as caixas de colisão; teste do João | J7, I8 |
| 9 ✅ | `docs/log-fase-1` | ✅ na Fase 1 e registro final | — |

Se não houver um controle de videogame para o teste manual, o suporte a controle é testado com um controle simulado e conferido depois.

### 10.2 Plano da Fase 2 (aprovado e concluído em 2026-10-16)

Um PR por item, cada um com testes, entrada no LOG e CI verde. A luta usa formas simples; a arte do Dom entra na Fase 3.

| # | Branch | Entrega | Itens |
|---|--------|---------|-------|
| 0 ✅ | `docs/plano-fase-2` (PR #13) | Este plano e as decisões D28 a D35 | — |
| 1 ✅ | `feat/chefe-e-fases` (PR #14) | Chefe genérico: vida, fases por limite, transição invulnerável, movimento por rota e dano por contato; a batalha passa a aceitar chefe além do boneco | D28 |
| 2 ✅ | `feat/padroes-de-ataque` (PR #15) | Peças de ataque com aviso (rajada, leque, mirado, chuva, zona, inimigos menores), lista de ataques por fase sorteada com semente, validação dos dados e teste do aviso mínimo | J6, D29, D30, D34 |
| 3 ✅ | `feat/modos` (PR #16) | Modos Normal e Simples, com teste de que as 3 fases se mantêm | J13, D13, D31 |
| 4 ✅ | `feat/dom-obsolescencio` (PR #17) | O Dom em dados: Torre de Tubos, Enxame Descontinuado (celulares destrutíveis e baterias estufadas que explodem) e Placa-Mãe (trilhas elétricas e a barra de "Atualização Obrigatória") | J8 |
| 5 ✅ | `feat/nota` (PR #18) | Nota da luta (A+ a D) com o modo ao lado | J14, D32 |
| 6 ✅ | `feat/voce-sabia` (PR #19) | Mecanismo do "Você sabia?": `fatos.toml` com fonte obrigatória por teste, sorteio sem repetição por chefe e mensagens neutras enquanto não houver fatos; os fatos vêm do João ou do grupo | J15, D35, C1 |
| 7 ✅ | `feat/telas-da-luta` (PR #20) | Tela da luta com o Dom em formas simples (sem vida do chefe na tela), escolha de modo, tela de derrota com barra de progresso, marcos de fase e "Você sabia?" com "tentar de novo" imediato, tela de vitória com nota e estatísticas, título com menu; teste do João nas 3 fases e nos dois modos | I6, I7, D17, D33, R5 |
| 8 ✅ | `docs/log-fase-2` | ✅ na Fase 2 e registro final | — |
