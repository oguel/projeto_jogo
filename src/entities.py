"""
entidades.py / entities.py — Jogador, NPCs, Diálogos e Animais.
"""
import pygame
import random
import math
import os

from src.constants import (
    TAM_TILE, PRECOS_VENDA, PRECOS_COMPRA, CUSTO_ANIMAIS, CUSTO_REPARO,
    ESTABULO_QUEBRADO, ESTABULO_FIXO, GALINHEIRO_QUEBRADO, GALINHEIRO_FIXO,
    ID_SEMENTE, ID_SEMENTE_ESP, ID_MUDA,
    ID_PEIXE_COMUM, ID_PEIXE_DOURADO, ID_PEIXE_RARO,
    ID_COLHEITA, ID_COLHEITA_ESP, ID_MADEIRA,
    RET_ESTABULO, RET_GALINHEIRO,
)
from src import assets as RECURSOS

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Jogador — sprite direcional, um único jogador
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LARG_JOG = 32
ALT_JOG  = 48

class Jogador:
    def __init__(self, genero: int):
        self.genero       = genero        # 0 = homem, 1 = mulher
        self.x: float    = 300.0
        self.y: float    = 280.0
        self.velocidade   = 4
        self.direcao      = 'baixo'       # 'cima' | 'baixo' | 'esquerda' | 'direita'
        self.pescando     = False
        self._prefixo     = 'jogador_m' if genero == 0 else 'jogador_f'
        self._cor         = (0, 100, 255) if genero == 0 else (255, 100, 200)
        self._tick_anim   = 0

    def mover(self, teclas_pressionadas, mapa_teclas: dict,
              colisoes: list | None = None):
        """Move o jogador com base nas teclas pressionadas."""
        dx = dy = 0
        if teclas_pressionadas[mapa_teclas.get('esquerda', pygame.K_a)]:  dx -= self.velocidade
        if teclas_pressionadas[mapa_teclas.get('direita',  pygame.K_d)]:  dx += self.velocidade
        if teclas_pressionadas[mapa_teclas.get('cima',     pygame.K_w)]:  dy -= self.velocidade
        if teclas_pressionadas[mapa_teclas.get('baixo',    pygame.K_s)]:  dy += self.velocidade

        if   dx < 0: self.direcao = 'esquerda'
        elif dx > 0: self.direcao = 'direita'
        elif dy < 0: self.direcao = 'cima'
        elif dy > 0: self.direcao = 'baixo'

        if dx or dy:
            self._tick_anim += 1

        novo_x, novo_y = self.x + dx, self.y + dy
        ret = pygame.Rect(int(novo_x), int(novo_y), LARG_JOG, ALT_JOG)
        if colisoes and any(ret.colliderect(col) for col in colisoes):
            return
        self.x, self.y = novo_x, novo_y

    def posicao_tile(self) -> tuple[int, int]:
        """Retorna a posição do jogador em coordenadas de tile."""
        return (int((self.x + LARG_JOG // 2) // TAM_TILE),
                int((self.y + ALT_JOG)         // TAM_TILE))

    def obter_ret(self) -> pygame.Rect:
        """Retorna o retângulo de colisão do jogador."""
        return pygame.Rect(int(self.x), int(self.y), LARG_JOG, ALT_JOG)

    def desenhar(self, tela: pygame.Surface):
        """Desenha o jogador (PNG ou procedural)."""
        # Mapeia direção para chave de recurso
        mapa_direcao = {
            'cima':     'cima',
            'baixo':    'baixo',
            'esquerda': 'esq',
            'direita':  'dir',
        }
        sufixo  = mapa_direcao.get(self.direcao, 'baixo')
        chave   = f'{self._prefixo}_{sufixo}'
        caminho = RECURSOS.CAMINHOS_IMG.get(chave, '')
        if caminho and os.path.isfile(caminho):
            surf = RECURSOS.obter_imagem(chave, (LARG_JOG, ALT_JOG))
            tela.blit(surf, (int(self.x), int(self.y)))
        else:
            self._desenhar_procedural(tela)

    def _desenhar_procedural(self, tela: pygame.Surface):
        """Desenha o sprite do jogador proceduralmente (sem PNG)."""
        x, y   = int(self.x), int(self.y)
        cor    = self._cor
        pele   = (255, 220, 180)
        cabelo = (80, 50, 20)   if self.genero == 0 else (200, 80, 160)
        calca  = (30, 30, 80)   if self.genero == 0 else (180, 30, 80)
        sapato = (40, 30, 20)
        quique = int(math.sin(self._tick_anim * 0.3) * 2)

        if self.direcao in ('baixo', 'cima'):
            pygame.draw.rect(tela, calca,  (x+6,  y+30+quique, 8,  14))
            pygame.draw.rect(tela, calca,  (x+18, y+30+quique, 8,  14))
            pygame.draw.rect(tela, sapato, (x+5,  y+42+quique, 10, 6))
            pygame.draw.rect(tela, sapato, (x+17, y+42+quique, 10, 6))
            pygame.draw.rect(tela, cor,    (x+4,  y+14, 24, 17))
            pygame.draw.rect(tela, cor,    (x,    y+14, 6,  14))
            pygame.draw.rect(tela, cor,    (x+26, y+14, 6,  14))
            pygame.draw.circle(tela, pele, (x+16, y+9), 10)
            if self.direcao == 'baixo':
                pygame.draw.circle(tela, (50,50,50), (x+12, y+8), 2)
                pygame.draw.circle(tela, (50,50,50), (x+20, y+8), 2)
                pygame.draw.arc(tela, (200,80,80),
                                pygame.Rect(x+11,y+11,10,5), math.pi, 0, 2)
            pygame.draw.ellipse(tela, cabelo, (x+6, y, 20, 12))

        elif self.direcao == 'direita':
            pygame.draw.rect(tela, calca,  (x+10, y+30+quique, 9, 14))
            pygame.draw.rect(tela, calca,  (x+19, y+32+quique, 9, 12))
            pygame.draw.rect(tela, sapato, (x+9,  y+42+quique, 11, 6))
            pygame.draw.rect(tela, sapato, (x+18, y+42+quique, 11, 6))
            pygame.draw.rect(tela, cor,    (x+8,  y+14, 18, 17))
            pygame.draw.rect(tela, cor,    (x+24, y+14, 8,  12))
            pygame.draw.circle(tela, pele, (x+18, y+9), 10)
            pygame.draw.ellipse(tela, cabelo, (x+10, y, 22, 12))
            pygame.draw.circle(tela, (50,50,50), (x+24, y+9), 2)

        elif self.direcao == 'esquerda':
            pygame.draw.rect(tela, calca,  (x+13, y+30+quique, 9, 14))
            pygame.draw.rect(tela, calca,  (x+4,  y+32+quique, 9, 12))
            pygame.draw.rect(tela, sapato, (x+12, y+42+quique, 11, 6))
            pygame.draw.rect(tela, sapato, (x+3,  y+42+quique, 11, 6))
            pygame.draw.rect(tela, cor,    (x+6,  y+14, 18, 17))
            pygame.draw.rect(tela, cor,    (x,    y+14, 8,  12))
            pygame.draw.circle(tela, pele, (x+14, y+9), 10)
            pygame.draw.ellipse(tela, cabelo, (x, y, 22, 12))
            pygame.draw.circle(tela, (50,50,50), (x+8, y+9), 2)

        # Vara de pesca (quando pescando virado para a direita)
        if self.pescando and self.direcao == 'direita':
            pygame.draw.line(tela, (120,80,30),   (x+32, y+20), (x+64, y+16), 3)
            pygame.draw.line(tela, (220,220,220), (x+64, y+16), (x+70, y+30), 1)
            pygame.draw.circle(tela, (255,50,50), (x+70, y+30), 3)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Diálogo — caixas de conversa com NPCs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class OpcaoDialogo:
    """Uma opção clicável dentro de um diálogo de NPC."""
    def __init__(self, rotulo: str, acao, habilitado: bool = True):
        self.rotulo    = rotulo
        self.acao      = acao
        self.habilitado = habilitado


class DialogoNPC:
    """Caixa de diálogo com lista de opções (mouse + teclado)."""
    LARG = 440
    ALT  = 320

    def __init__(self, titulo: str, opcoes: list):
        self.titulo    = titulo
        self.opcoes    = list(opcoes)
        self.selecionado = 0
        self.mensagem  = ''
        self.timer_msg = 0
        # Sempre adiciona a opção "Fechar" no final se não existir
        if not any(o.rotulo == 'Fechar' for o in self.opcoes):
            self.opcoes.append(OpcaoDialogo('Fechar', lambda dados: None))

    def processar_eventos(self, eventos: list, teclas: dict) -> bool:
        """
        Processa eventos do diálogo.
        Retorna False quando o diálogo deve ser fechado.
        """
        largura, altura = 800, 600
        bx    = largura // 2 - self.LARG // 2
        by    = altura  // 2 - self.ALT  // 2
        alt_linha = 34

        for evento in eventos:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                mx, my = evento.pos
                for i, opcao in enumerate(self.opcoes):
                    linha_y = by + 60 + i * alt_linha
                    if bx <= mx <= bx + self.LARG and linha_y <= my <= linha_y + alt_linha:
                        self.selecionado = i
                        if opcao.rotulo == 'Fechar':
                            return False
                        if opcao.habilitado:
                            resultado       = opcao.acao(None)
                            self.mensagem   = resultado or ''
                            self.timer_msg  = pygame.time.get_ticks()
                        break

            elif evento.type == pygame.KEYDOWN:
                tecla_cima     = teclas.get('cima',     pygame.K_w)
                tecla_baixo    = teclas.get('baixo',    pygame.K_s)
                tecla_interagir = teclas.get('interagir', pygame.K_e)

                if evento.key in (tecla_cima, pygame.K_UP):
                    self.selecionado = (self.selecionado - 1) % len(self.opcoes)
                elif evento.key in (tecla_baixo, pygame.K_DOWN):
                    self.selecionado = (self.selecionado + 1) % len(self.opcoes)
                elif evento.key in (tecla_interagir, pygame.K_RETURN):
                    opcao = self.opcoes[self.selecionado]
                    if opcao.rotulo == 'Fechar':
                        return False
                    if opcao.habilitado:
                        resultado       = opcao.acao(None)
                        self.mensagem   = resultado or ''
                        self.timer_msg  = pygame.time.get_ticks()
                elif evento.key == pygame.K_ESCAPE:
                    return False

        return True

    def desenhar(self, tela: pygame.Surface, fontes: dict):
        """Desenha a caixa de diálogo na tela."""
        largura, altura = tela.get_size()
        bx = largura // 2 - self.LARG // 2
        by = altura  // 2 - self.ALT  // 2
        alt_linha = 34
        mx, my    = pygame.mouse.get_pos()

        fundo = pygame.Surface((self.LARG, self.ALT), pygame.SRCALPHA)
        fundo.fill((18, 18, 40, 240))
        pygame.draw.rect(fundo, (80, 80, 180), fundo.get_rect(), 3, border_radius=14)
        tela.blit(fundo, (bx, by))

        fonte_g = fontes.get('grande', pygame.font.SysFont('arial', 24, bold=True))
        fonte_n = fontes.get('normal', pygame.font.SysFont('arial', 18))
        fonte_p = fontes.get('pequena', pygame.font.SysFont('arial', 14))

        titulo = fonte_g.render(self.titulo, True, (255, 240, 140))
        tela.blit(titulo, (bx + self.LARG // 2 - titulo.get_width() // 2, by + 12))

        for i, opcao in enumerate(self.opcoes):
            linha_y = by + 60 + i * alt_linha
            hover  = bx <= mx <= bx + self.LARG and linha_y <= my <= linha_y + alt_linha
            sel    = i == self.selecionado
            cor_fundo = (60, 60, 180, 160) if sel else (40, 40, 80, 80) if hover else (0, 0, 0, 0)
            bg_linha  = pygame.Surface((self.LARG - 16, alt_linha - 2), pygame.SRCALPHA)
            bg_linha.fill(cor_fundo)
            tela.blit(bg_linha, (bx + 8, linha_y + 1))
            cor   = (255, 255, 100) if sel else (200, 200, 200) if opcao.habilitado else (100, 100, 100)
            pref  = '▶ ' if sel else '  '
            linha = fonte_n.render(pref + opcao.rotulo, True, cor)
            tela.blit(linha, (bx + 18, linha_y + 6))

        if self.mensagem and pygame.time.get_ticks() - self.timer_msg < 2500:
            msg = fonte_p.render(self.mensagem, True, (100, 255, 150))
            tela.blit(msg, (bx + 12, by + self.ALT - 28))

        dica = fonte_p.render('↑↓ = navegar  E/Enter = selecionar  ESC = fechar', True, (70, 70, 70))
        tela.blit(dica, (bx + self.LARG // 2 - dica.get_width() // 2, by + self.ALT - 14))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NPCs — base
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LARG_NPC = 32
ALT_NPC  = 48

class NPCBase:
    def __init__(self, nome: str, chave_recurso: str, x: int, y: int):
        self.nome           = nome
        self.chave_recurso  = chave_recurso
        self.x, self.y     = x, y
        self.ret_interacao  = pygame.Rect(x - 36, y - 24, LARG_NPC + 72, ALT_NPC + 48)

    def desenhar(self, tela: pygame.Surface, fontes: dict, jogador_perto: bool = False):
        """Desenha o NPC com nome flutuante."""
        caminho = RECURSOS.CAMINHOS_IMG.get(self.chave_recurso, '')
        if caminho and os.path.isfile(caminho):
            tela.blit(RECURSOS.obter_imagem(self.chave_recurso, (LARG_NPC, ALT_NPC)),
                       (self.x, self.y))
        else:
            self._desenhar_placeholder(tela)

        fonte_p = fontes.get('pequena', pygame.font.SysFont('arial', 13))
        rotulo  = fonte_p.render(self.nome, True, (255, 255, 200))
        tela.blit(rotulo, (self.x + LARG_NPC // 2 - rotulo.get_width() // 2, self.y - 18))
        if jogador_perto:
            dica = fonte_p.render('[E] Falar', True, (180, 255, 180))
            tela.blit(dica, (self.x + LARG_NPC // 2 - dica.get_width() // 2, self.y + ALT_NPC + 4))

    def _desenhar_placeholder(self, tela: pygame.Surface):
        """Sprite procedural por tipo de NPC."""
        mapa_cor = {
            'npc_fazendeiro': (200, 160, 50),
            'npc_pescador':   (50,  150, 220),
            'npc_vendedor':   (120, 200, 70),
            'npc_construtor': (210, 100, 50),
        }
        cor  = mapa_cor.get(self.chave_recurso, (180, 180, 180))
        pele = (255, 220, 180)
        x, y = self.x, self.y
        pygame.draw.rect(tela, (50, 50, 100), (x+6, y+30, 8, 18))
        pygame.draw.rect(tela, (50, 50, 100), (x+18, y+30, 8, 18))
        pygame.draw.rect(tela, cor,  (x+4, y+14, 24, 17))
        pygame.draw.circle(tela, pele, (x+16, y+9), 10)
        if 'fazendeiro' in self.chave_recurso:
            pygame.draw.rect(tela, (100, 70, 20), (x+4, y-2, 24, 8))
            pygame.draw.rect(tela, (120, 85, 25), (x+2, y+4, 28, 4))
        elif 'pescador' in self.chave_recurso:
            pygame.draw.ellipse(tela, (50, 120, 200), (x+2, y-4, 28, 14))
        elif 'vendedor' in self.chave_recurso:
            pygame.draw.circle(tela, (80, 180, 50), (x+16, y-2), 8)
        elif 'construtor' in self.chave_recurso:
            pygame.draw.rect(tela, (255, 200, 0), (x+4, y-4, 24, 10))

    def esta_perto(self, jogador) -> bool:
        """Verifica se o jogador está próximo o suficiente para interagir."""
        return self.ret_interacao.colliderect(jogador.obter_ret())

    def obter_dialogo(self, dados_jogo) -> DialogoNPC:
        return DialogoNPC(self.nome, [])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NPCs específicos
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class NPCFazendeiro(NPCBase):
    def __init__(self, x, y):
        super().__init__('Fazendeiro', 'npc_fazendeiro', x, y)

    def obter_dialogo(self, dados_jogo) -> DialogoNPC:
        inv = dados_jogo.inventario

        def comprar(id_item, preco, atributo):
            def _comprar(dados):
                if inv.dinheiro >= preco:
                    inv.dinheiro -= preco
                    setattr(inv, atributo, getattr(inv, atributo) + 1)
                    return f'Comprado! Dinheiro: ${inv.dinheiro}'
                return f'Precisa de ${preco}!'
            return _comprar

        return DialogoNPC('🧑‍🌾 Fazendeiro', [
            OpcaoDialogo(f'Semente (${PRECOS_COMPRA[ID_SEMENTE]})',
                         comprar(ID_SEMENTE, PRECOS_COMPRA[ID_SEMENTE], 'semente')),
            OpcaoDialogo(f'Semente Especial (${PRECOS_COMPRA[ID_SEMENTE_ESP]})',
                         comprar(ID_SEMENTE_ESP, PRECOS_COMPRA[ID_SEMENTE_ESP], 'semente_esp')),
            OpcaoDialogo(f'Muda de Árvore (${PRECOS_COMPRA[ID_MUDA]})',
                         comprar(ID_MUDA, PRECOS_COMPRA[ID_MUDA], 'muda')),
        ])


class NPCPescador(NPCBase):
    def __init__(self, x, y):
        super().__init__('Pescador', 'npc_pescador', x, y)

    def obter_dialogo(self, dados_jogo) -> DialogoNPC:
        inv        = dados_jogo.inventario
        preco_vara = 30

        def comprar_vara(dados):
            if dados_jogo.tem_vara:
                return 'Você já tem uma vara de pesca!'
            if inv.dinheiro >= preco_vara:
                inv.dinheiro         -= preco_vara
                dados_jogo.tem_vara   = True
                return 'Vara comprada! Vá até o pier e pressione F.'
            return f'Precisa de ${preco_vara}!'

        def vender_peixes(dados):
            tipos  = {ID_PEIXE_COMUM:   PRECOS_VENDA[ID_PEIXE_COMUM],
                      ID_PEIXE_DOURADO:  PRECOS_VENDA[ID_PEIXE_DOURADO],
                      ID_PEIXE_RARO:     PRECOS_VENDA[ID_PEIXE_RARO]}
            total  = sum(inv.quantidade(t) * p for t, p in tipos.items())
            for t in tipos:
                inv.remover(t, inv.quantidade(t))
            inv.dinheiro += total
            return f'Vendeu peixes: ${total}!' if total else 'Sem peixes para vender.'

        rotulo_vara = f'Vara de Pesca (${preco_vara})' + \
                      (' ✅ Comprada' if dados_jogo.tem_vara else '')
        return DialogoNPC('🎣 Pescador', [
            OpcaoDialogo(rotulo_vara, comprar_vara, habilitado=not dados_jogo.tem_vara),
            OpcaoDialogo('Vender todos os peixes', vender_peixes),
        ])


class NPCVendedorAnimais(NPCBase):
    def __init__(self, x, y):
        super().__init__('Vendedor de Animais', 'npc_vendedor', x, y)

    def obter_dialogo(self, dados_jogo) -> DialogoNPC:
        inv     = dados_jogo.inventario
        predios = dados_jogo.predios
        opcoes  = []

        for tipo_animal, info in CUSTO_ANIMAIS.items():
            def criar_compra(a=tipo_animal, dados_animal=info):
                def comprar(dados):
                    # Verifica se o prédio está consertado
                    predio_req_quebrado = ESTABULO_QUEBRADO if dados_animal['predio'] == ESTABULO_FIXO \
                                         else GALINHEIRO_QUEBRADO
                    if predios.get(predio_req_quebrado) != dados_animal['predio']:
                        nome_predio = 'estábulo' if dados_animal['predio'] == ESTABULO_FIXO else 'galinheiro'
                        return f'Conserte o {nome_predio} primeiro!'
                    if inv.dinheiro >= dados_animal['dinheiro']:
                        inv.dinheiro -= dados_animal['dinheiro']
                        import random as _r
                        if a == 'galinha':
                            # Nasce dentro do galinheiro
                            ax, ay = _r.uniform(210, 300), _r.uniform(8, 100)
                        else:
                            # Nasce dentro do estábulo
                            ax, ay = _r.uniform(8, 145), _r.uniform(290, 420)
                        dados_jogo.animais.append({
                            'tipo': a, 'x': ax, 'y': ay,
                            'vx': _r.uniform(-1, 1),
                            'vy': _r.uniform(-1, 1),
                        })
                        return f'{dados_animal["nome"]} comprado!'
                    return f'Precisa de ${dados_animal["dinheiro"]}!'
                return comprar
            opcoes.append(OpcaoDialogo(f'{info["nome"]} (${info["dinheiro"]})', criar_compra()))

        return DialogoNPC('🐄 Vendedor de Animais', opcoes)


class NPCConstrutor(NPCBase):
    def __init__(self, x, y):
        super().__init__('Construtor', 'npc_construtor', x, y)

    def obter_dialogo(self, dados_jogo) -> DialogoNPC:
        inv     = dados_jogo.inventario
        predios = dados_jogo.predios
        opcoes  = []

        reparos = [
            (ESTABULO_QUEBRADO,   ESTABULO_FIXO,   'Estábulo'),
            (GALINHEIRO_QUEBRADO, GALINHEIRO_FIXO, 'Galinheiro'),
        ]
        for chave_quebrado, chave_fixo, nome_predio in reparos:
            custo = CUSTO_REPARO[chave_quebrado]
            if predios.get(chave_quebrado) == chave_fixo:
                opcoes.append(OpcaoDialogo(f'{nome_predio} ✅ (consertado)',
                                           lambda dados: None, habilitado=False))
            else:
                def criar_reparo(cq=chave_quebrado, cf=chave_fixo, c=custo, n=nome_predio):
                    def reparar(dados):
                        if inv.dinheiro >= c['dinheiro'] and inv.madeira >= c['madeira']:
                            inv.dinheiro -= c['dinheiro']
                            inv.madeira  -= c['madeira']
                            predios[cq]   = cf
                            return f'{n} consertado!'
                        return f'Precisa ${c["dinheiro"]} + {c["madeira"]} madeiras'
                    return reparar
                opcoes.append(OpcaoDialogo(
                    f'Consertar {nome_predio} (${custo["dinheiro"]} + {custo["madeira"]} 🪵)',
                    criar_reparo()))

        return DialogoNPC('🔨 Construtor', opcoes)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Animais — movimentação dentro dos prédios
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Área de movimentação de cada tipo de animal calculada dinamicamente
# com base nas posições reais dos prédios em pixels.
def _calc_area_animal(ret_tiles: tuple, margem: int = 6) -> pygame.Rect:
    """Converte um ret de tiles (col, lin, larg, alt) para pixels com margem interna."""
    col, lin, larg, alt = ret_tiles
    px = col * TAM_TILE + margem
    py = lin * TAM_TILE + margem
    pw = larg * TAM_TILE - margem * 2
    ph = alt  * TAM_TILE - margem * 2
    return pygame.Rect(px, py, pw, ph)


AREA_POR_TIPO = {
    'galinha': _calc_area_animal(RET_GALINHEIRO),
    'vaca':    _calc_area_animal(RET_ESTABULO),
}

TAMANHO_ANIMAL = 20   # tamanho de desenho do animal em pixels


def atualizar_animais(lista_animais: list):
    """Move cada animal dentro da sua área de confinamento."""
    for animal in lista_animais:
        tipo = animal.get('tipo', 'galinha')
        area = AREA_POR_TIPO.get(tipo)
        if not area:
            continue

        animal['x'] += animal['vx']
        animal['y'] += animal['vy']

        # Ricochete nas bordas da área
        if animal['x'] < area.x or animal['x'] > area.right  - TAMANHO_ANIMAL:
            animal['vx'] = -animal['vx']
            animal['x']  = max(area.x, min(area.right  - TAMANHO_ANIMAL, animal['x']))
        if animal['y'] < area.y or animal['y'] > area.bottom - TAMANHO_ANIMAL:
            animal['vy'] = -animal['vy']
            animal['y']  = max(area.y, min(area.bottom - TAMANHO_ANIMAL, animal['y']))

        # Pequena chance de mudar direção aleatoriamente
        if random.random() < 0.005:
            animal['vx'] = random.uniform(-1.2, 1.2)
            animal['vy'] = random.uniform(-1.2, 1.2)


def desenhar_animais(tela: pygame.Surface, lista_animais: list):
    """Desenha cada animal na tela (procedural se sem PNG)."""
    for animal in lista_animais:
        ax   = int(animal['x'])
        ay   = int(animal['y'])
        tipo = animal.get('tipo', 'galinha')

        if tipo == 'vaca':
            chave = 'animal_vaca'
            caminho = RECURSOS.CAMINHOS_IMG.get(chave, '')
            if caminho and os.path.isfile(caminho):
                tela.blit(RECURSOS.obter_imagem(chave, (TAMANHO_ANIMAL + 8, TAMANHO_ANIMAL)),
                           (ax, ay))
            else:
                # Vaca procedural (marrom-bege com manchas)
                pygame.draw.ellipse(tela, (210, 188, 140), (ax, ay + 6, 28, 14))
                pygame.draw.circle(tela, (220, 195, 150), (ax + 24, ay + 8), 7)
                pygame.draw.ellipse(tela, (80,  60,  30),  (ax + 6, ay + 4, 8, 6))
                pygame.draw.ellipse(tela, (80,  60,  30),  (ax +14, ay + 8, 7, 5))
                pygame.draw.line(tela, (160, 130, 90), (ax+4, ay+20), (ax+4,  ay+30), 2)
                pygame.draw.line(tela, (160, 130, 90), (ax+10,ay+20), (ax+10, ay+30), 2)
                pygame.draw.line(tela, (160, 130, 90), (ax+18,ay+20), (ax+18, ay+30), 2)
                pygame.draw.line(tela, (160, 130, 90), (ax+24,ay+20), (ax+24, ay+30), 2)

        elif tipo == 'galinha':
            chave   = 'animal_galinha'
            caminho = RECURSOS.CAMINHOS_IMG.get(chave, '')
            if caminho and os.path.isfile(caminho):
                tela.blit(RECURSOS.obter_imagem(chave, (TAMANHO_ANIMAL, TAMANHO_ANIMAL)),
                           (ax, ay))
            else:
                # Galinha procedural (branca)
                pygame.draw.ellipse(tela, (248, 242, 232), (ax, ay + 4, 18, 12))
                pygame.draw.circle(tela, (250, 245, 235), (ax + 16, ay + 6), 7)
                pygame.draw.polygon(tela, (255, 160, 40), [
                    (ax+22, ay+6), (ax+26, ay+4), (ax+26, ay+8)])
                pygame.draw.circle(tela, (220, 60, 60), (ax+18, ay+2), 3)
                pygame.draw.line(tela, (210, 180, 140), (ax+4, ay+16), (ax+4,  ay+22), 2)
                pygame.draw.line(tela, (210, 180, 140), (ax+10,ay+16), (ax+10, ay+22), 2)
