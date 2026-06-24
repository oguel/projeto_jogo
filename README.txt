# 🌾 Fazenda — Vida no Campo

Um jogo de fazenda 2D feito em Python com Pygame. Plante, colha, críe animais, pesque e administre sua propriedade do zero!

---

## 🎮 Sobre o Jogo

Você acabou de comprar uma antiga fazenda em leilão. A partir daí, é com você:
arar a terra, plantar sementes, esperar o crescimento, colher, vender na cidade, reparar os prédios, comprar animais e pescar no lago. O dia passa e à meia-noite você desmaia de cansaço — então durma cedo!

---

## 🕹️ Como Jogar

### Pré-requisitos

- Python 3.11 ou superior  
- Pygame 2.x

```bash
pip install pygame
```

### Executar

```bash
python jogo.py
```

---

## ⌨️ Controles (padrão)

| Tecla | Ação |
|-------|------|
| W / A / S / D | Mover o personagem |
| E | Interagir (arar terra, dormir na cama, vender) |
| P | Plantar semente ativa |
| C | Colher plantação pronta |
| X | Cortar árvore (madeira) |
| F | Pescar (quando estiver no pier, olhando para a direita) |
| TAB | Ciclar entre sementes (Trigo → Cenoura → Muda) |
| I | Abrir/fechar painel de inventário |
| ESC | Abrir configurações (ou fechar menus) |
| F12 | Cheat de debug (+$200 e +50 madeiras) |

> Os controles podem ser remapeados nas **Configurações** (ESC na tela inicial ou durante o jogo).

---

## 🌱 Jogabilidade

### Fazenda

- **Arar:** Pressione `E` sobre um tile de grama para virar solo.
- **Plantar:** Selecione a semente com `TAB` e pressione `P` no solo arado.
- **Colher:** Pressione `C` quando a barra de progresso do tile encher.
- **Árvores:** Plant uma muda (`P`), espere virar árvore e corte com `X`.
- **Dormir:** Entre na casa e fique perto da cama; pressione `E`.
- **Vender (rápido):** Encoste na caixa dourada no canto superior direito e pressione `E`.

### Cidade

Vá para a cidade atravessando a borda direita da fazenda. Lá você encontra:

| NPC | Localização | O que faz |
|-----|-------------|-----------|
| **Fazendeiro** | Canto NO | Compra sementes, vende colheitas |
| **Pescador** | Canto NE | Vende vara de pesca, compra peixes |
| **Construtor** | Canto SO | Conserta Estábulo e Galinheiro |
| **Vendedor de Animais** | Canto SE | Vende vacas e galinhas |

Aproxime-se de um prédio e pressione `ENTER` para entrar na loja.

### Pesca

1. Compre uma vara de pesca com o Pescador ($30).
2. Vá até o **pier** (a ponte de madeira no lago da fazenda).
3. Posicione-se na coluna certa, olhando para a **direita**, e pressione `F`.
4. Minigame de ritmo: acerte as notas nas 4 pistas (A / S / W / D).
5. Encha a barra antes de errar 3 rounds completos.

### Animais

- Conserte o **Estábulo** (vacas) e o **Galinheiro** (galinhas) com o Construtor.
- Compre os animais no Vendedor de Animais.
- Os animais ficam visíveis e se movem quando você entra nos prédios.

---

## 💾 Save & Config

- O progresso é salvo automaticamente ao **dormir**, ao **entrar na cidade** e à **meia-noite**.
- Arquivo de save: `save.json` (na raiz do projeto).
- Arquivo de configuração: `config.json`.
- Para **resetar** o jogo: apague o `save.json`.

---

## ⏰ Sistema de Tempo

- O dia começa às **08:00** e termina à **meia-noite (00:00)**.
- Cada tick de jogo = 10 minutos internos / 5 segundos reais.
- Às **23:00** você recebe um aviso de cansaço.
- À **00:00** o personagem desmaia e acorda no dia seguinte.

---

## 📁 Estrutura do Projeto

```
projeto_jogo/
├── jogo.py              # Ponto de entrada principal
├── config.json          # Configurações salvas (teclas, volume, tela)
├── save.json            # Save do jogo
├── src/
│   ├── constants.py     # Todas as constantes do jogo
│   ├── states.py        # Estados: Título, Intro, Desmaio
│   ├── farm_state.py    # Estado principal: a fazenda
│   ├── town_state.py    # Estado da cidade e NPCs visuais
│   ├── fishing_state.py # Minigame de pesca (ritmo)
│   ├── entities.py      # Jogador, NPCs, Inventário, Animais, Diálogos
│   ├── game_data.py     # Dados globais: save/load, inventário, horário
│   ├── assets.py        # Carregamento e cache de imagens e sons
│   └── settings_state.py# Tela de configurações
└── assets/
    ├── images/          # Sprites organizados por categoria
    └── sounds/          # Músicas e efeitos sonoros
```

---

## 🐟 Tipos de Peixe

| Peixe | Dificuldade | Valor de venda |
|-------|-------------|----------------|
| Peixinho (comum) | Fácil (55 BPM) | $8 |
| Peixe Dourado | Médio (80 BPM) | $25 |
| Peixe Raro | Difícil (110 BPM) | $60 |

---

## 💰 Preços

### Compra (cidade)
| Item | Preço |
|------|-------|
| Semente de Trigo | $2 |
| Semente de Cenoura | $8 |
| Muda de Árvore | $5 |
| Vara de Pesca | $30 |

### Venda (cidade ou caixa da fazenda)
| Item | Preço |
|------|-------|
| Trigo colhido | $5 |
| Cenoura colhida | $15 |
| Madeira | $3 |
| Peixe Comum | $8 |
| Peixe Dourado | $25 |
| Peixe Raro | $60 |

---

## 📝 Versão

**v0.4** — Jogo em desenvolvimento.
