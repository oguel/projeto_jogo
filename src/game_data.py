import json
import os
import pygame

from src.constants import (
    TECLAS_PADRAO, VOLUMES_PADRAO, PADROES_PESCA_PADRAO,
    PRECOS_VENDA,
    ID_SEMENTE, ID_SEMENTE_ESP, ID_MUDA,
    ID_COLHEITA, ID_COLHEITA_ESP, ID_MADEIRA,
    ID_PEIXE_COMUM, ID_PEIXE_DOURADO, ID_PEIXE_RARO,
    HORA_INICIO, HORA_FIM, SEGUNDOS_POR_TICK, MINUTOS_POR_TICK,
    ESTABULO_QUEBRADO, GALINHEIRO_QUEBRADO,
)

CAMINHO_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'config.json'
)
CAMINHO_SAVE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'save.json'
)


# Configuracao - teclas, audio, tela

class Configuracao:
    def __init__(self):
        self.teclas            = dict(TECLAS_PADRAO)
        self.volumes           = dict(VOLUMES_PADRAO)
        self.padroes_pesca     = dict(PADROES_PESCA_PADRAO)
        self.tela_cheia        = False
        self.mudanca_resolucao = False
        self.carregar()

    def salvar(self):
        dados = {
            'teclas':     {acao: tecla for acao, tecla in self.teclas.items()},
            'volumes':    self.volumes,
            'tela_cheia': self.tela_cheia,
        }
        try:
            with open(CAMINHO_CONFIG, 'w', encoding='utf-8') as arq:
                json.dump(dados, arq, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def carregar(self):
        if not os.path.isfile(CAMINHO_CONFIG):
            return
        try:
            with open(CAMINHO_CONFIG, encoding='utf-8') as arq:
                dados = json.load(arq)
            if 'teclas' in dados:
                for acao, tecla in dados['teclas'].items():
                    self.teclas[acao] = int(tecla)
            if 'volumes' in dados:
                self.volumes.update(dados['volumes'])
            if 'tela_cheia' in dados:
                self.tela_cheia = bool(dados['tela_cheia'])
        except Exception:
            pass


# Inventario - tudo que o jogador possui

CICLO_SEMENTES = [ID_SEMENTE, ID_SEMENTE_ESP, ID_MUDA]

class Inventario:
    def __init__(self):
        self.dinheiro         = 100
        self.semente          = 5
        self.semente_esp      = 0
        self.muda             = 0
        self.colheita         = 0
        self.colheita_esp     = 0
        self.madeira          = 0
        self.peixe_comum      = 0
        self.peixe_dourado    = 0
        self.peixe_raro       = 0
        self.semente_ativa    = ID_SEMENTE

    _NOME_SEMENTE = {
        ID_SEMENTE:     'Trigo',
        ID_SEMENTE_ESP: 'Cenoura',
        ID_MUDA:        'Muda',
    }

    def ciclar_semente(self):
        idx = CICLO_SEMENTES.index(self.semente_ativa)
        self.semente_ativa = CICLO_SEMENTES[(idx + 1) % len(CICLO_SEMENTES)]

    def quantidade(self, id_item: str) -> int:
        return getattr(self, id_item.replace('-', '_'), 0)

    def adicionar(self, id_item: str, qtd: int = 1):
        nome = id_item.replace('-', '_')
        if hasattr(self, nome):
            setattr(self, nome, getattr(self, nome) + qtd)

    def remover(self, id_item: str, qtd: int = 1):
        nome = id_item.replace('-', '_')
        if hasattr(self, nome):
            setattr(self, nome, max(0, getattr(self, nome) - qtd))

    def vender_tudo(self) -> int:
        total = 0
        for id_item, preco in PRECOS_VENDA.items():
            qtd = self.quantidade(id_item)
            if qtd > 0:
                total += qtd * preco
                self.remover(id_item, qtd)
        self.dinheiro += total
        return total

    def desenhar_hud(self, tela: pygame.Surface, fonte_pequena, fonte_normal=None, dia: int = 1):
        fonte_n = fonte_normal or fonte_pequena

        def _painel(texto, cor_texto, cor_borda, x, y, cor_icone=None):
            surf = fonte_pequena.render(texto, True, cor_texto)
            larg = surf.get_width() + (28 if cor_icone else 14)
            box  = pygame.Surface((larg, 24), pygame.SRCALPHA)
            box.fill((12, 10, 4, 210))
            pygame.draw.rect(box, cor_borda, box.get_rect(), 1, border_radius=5)
            tela.blit(box, (x, y))
            if cor_icone:
                pygame.draw.rect(tela, cor_icone, (x + 5, y + 6, 12, 12), border_radius=3)
                tela.blit(surf, (x + 21, y + 4))
            else:
                tela.blit(surf, (x + 7, y + 4))

        _painel(f'${self.dinheiro}',        (255, 230, 80),  (180, 150, 40), 4, 4,  (220, 185, 30))
        _painel(f'Dia {dia}',               (200, 220, 255), (80, 100, 160), 4, 32, (80, 120, 210))
        _painel(f'Madeira: {self.madeira}', (200, 170, 110), (120, 90,  40), 4, 60, (160, 110, 50))

        _COR_BORDA = {
            ID_SEMENTE:     (60, 200, 60),
            ID_SEMENTE_ESP: (200, 80, 220),
            ID_MUDA:        (50, 170, 90),
        }
        _COR_ICONE = {
            ID_SEMENTE:     (80, 200, 80),
            ID_SEMENTE_ESP: (200, 100, 220),
            ID_MUDA:        (60, 180, 100),
        }
        nome_sem  = self._NOME_SEMENTE.get(self.semente_ativa, '?')
        qtd_sem   = self.quantidade(self.semente_ativa)
        cor_txt   = (180, 255, 140) if qtd_sem > 0 else (160, 100, 100)
        cor_borda = _COR_BORDA.get(self.semente_ativa, (60, 130, 60))
        cor_icone = _COR_ICONE.get(self.semente_ativa, (80, 160, 80))
        txt_sem   = fonte_n.render(f'{nome_sem}  x{qtd_sem}', True, cor_txt)
        alt_tela  = tela.get_height()
        larg_box  = txt_sem.get_width() + 32
        alt_box   = 30
        box2      = pygame.Surface((larg_box, alt_box), pygame.SRCALPHA)
        box2.fill((4, 22, 4, 210))
        pygame.draw.rect(box2, cor_borda, box2.get_rect(), 2, border_radius=7)
        tela.blit(box2, (4, alt_tela - alt_box - 6))
        pygame.draw.rect(tela, cor_icone, (10, alt_tela - alt_box - 1, 14, 20), border_radius=3)
        tela.blit(txt_sem, (28, alt_tela - alt_box - 1))

    def desenhar_painel(self, tela: pygame.Surface, fontes: dict, tem_vara: bool):
        largura, altura = tela.get_size()
        larg_painel = 420
        alt_painel  = 460
        px = largura  // 2 - larg_painel // 2
        py = altura   // 2 - alt_painel  // 2

        fundo = pygame.Surface((larg_painel, alt_painel), pygame.SRCALPHA)
        fundo.fill((10, 14, 28, 248))
        pygame.draw.rect(fundo, (60, 70, 140), fundo.get_rect(), 2, border_radius=14)
        tela.blit(fundo, (px, py))

        fonte_g = fontes.get('grande',  pygame.font.SysFont('arial', 22, bold=True))
        fonte_n = fontes.get('normal',  pygame.font.SysFont('arial', 16))
        fonte_p = fontes.get('pequena', pygame.font.SysFont('arial', 13))

        titulo = fonte_g.render('INVENTARIO', True, (255, 235, 100))
        tela.blit(titulo, (px + larg_painel // 2 - titulo.get_width() // 2, py + 10))
        pygame.draw.line(tela, (60, 70, 140), (px + 12, py + 40), (px + larg_painel - 12, py + 40), 1)

        itens = [
            ('Dinheiro',        f'${self.dinheiro}',   (220, 185,  30)),
            ('Trigo (semente)', str(self.semente),     ( 80, 200,  80)),
            ('Cenoura (sem.)',  str(self.semente_esp), (200, 100, 220)),
            ('Muda de Arvore',  str(self.muda),        ( 60, 180, 100)),
            ('Trigo (colh.)',   str(self.colheita),    (240, 210,  50)),
            ('Cenoura (colh.)', str(self.colheita_esp),(240, 100,  60)),
            ('Madeira',         str(self.madeira),     (160, 110,  50)),
            ('Peixe Comum',     str(self.peixe_comum), ( 80, 160, 255)),
            ('Peixe Dourado',   str(self.peixe_dourado),(255, 200,  40)),
            ('Peixe Raro',      str(self.peixe_raro),  (180,  80, 240)),
            ('Vara de Pesca',   'SIM' if tem_vara else 'NAO',
                                (80, 220, 80) if tem_vara else (180, 80, 80)),
        ]

        col_larg = (larg_painel - 24) // 2
        for i, (rotulo, valor, cor_ic) in enumerate(itens):
            col  = i % 2
            iy   = py + 50 + (i // 2) * 38
            ix   = px + 12 + col * col_larg

            card = pygame.Surface((col_larg, 32), pygame.SRCALPHA)
            card.fill((20, 24, 48, 180))
            pygame.draw.rect(card, (*cor_ic, 80), card.get_rect(), 1, border_radius=6)
            tela.blit(card, (ix, iy))
            pygame.draw.rect(tela, cor_ic, (ix + 5, iy + 8, 10, 16), border_radius=3)
            tela.blit(fonte_p.render(rotulo, True, (190, 190, 210)), (ix + 20, iy + 4))
            cor_val = cor_ic if valor not in ('0', 'NAO') else (100, 100, 120)
            t_val = fonte_n.render(valor, True, cor_val)
            tela.blit(t_val, (ix + col_larg - t_val.get_width() - 8, iy + 10))

        dica = fonte_p.render('[ I ] ou [ ESC ] para fechar', True, (70, 70, 110))
        tela.blit(dica, (px + larg_painel // 2 - dica.get_width() // 2, py + alt_painel - 22))


# SistemaHorario - relogio interno do dia

class SistemaHorario:
    def __init__(self):
        self._hora_real_inicio  = pygame.time.get_ticks()
        self.hora               = HORA_INICIO
        self.minuto             = 0
        self.dia                = 1
        self.notificado_cansado = False

    def hora_atual(self) -> tuple[str, int, int]:
        ms_passados = pygame.time.get_ticks() - self._hora_real_inicio
        ticks       = ms_passados // (SEGUNDOS_POR_TICK * 1000)
        total_min   = HORA_INICIO * 60 + ticks * MINUTOS_POR_TICK
        hora        = (total_min // 60) % 24
        minuto      = total_min % 60
        return f'{hora:02d}:{minuto:02d}', hora, minuto

    def eh_meia_noite(self) -> bool:
        _, hora, _ = self.hora_atual()
        return hora >= HORA_FIM

    def hora_cansado(self) -> bool:
        _, hora, _ = self.hora_atual()
        return hora >= HORA_FIM - 1

    def nivel_escuridao(self) -> float:
        _, hora, _ = self.hora_atual()
        if hora < 18:
            return 0.0
        return min(1.0, (hora - 18) / 6)

    def reiniciar_dia(self):
        self.dia               += 1
        self.notificado_cansado = False
        self._hora_real_inicio  = pygame.time.get_ticks()


# DadosJogo - contentor global compartilhado entre estados

class DadosJogo:
    def __init__(self):
        self.configuracao  = Configuracao()
        self.inventario    = Inventario()
        self.horario       = SistemaHorario()

        self.mapa_fazenda  = None
        self.timer_plantas = {}   # (col, lin): timestamp em ms

        self.predios = {
            ESTABULO_QUEBRADO:   ESTABULO_QUEBRADO,
            GALINHEIRO_QUEBRADO: GALINHEIRO_QUEBRADO,
        }

        self.animais            = []
        self.jogador            = None
        self.msg_cansado        = False
        self.timer_msg_cansado  = 0
        self.dormiu_voluntario  = False
        self.tem_vara           = False
        self.ultimo_resultado   = None   # 'capturado' | 'escapou' | None
        self.ultimo_mapa        = 'fazenda'

        self.carregar()

    # Sistema de save/load - save.json
    # Para resetar o jogo: delete o arquivo save.json na pasta do jogo

    def salvar(self):
        inv = self.inventario
        hor = self.horario
        mapa_serial = self.mapa_fazenda if self.mapa_fazenda is not None else None
        tp_serial   = {
            f'{c},{l}': t for (c, l), t in self.timer_plantas.items()
        }
        dados = {
            'dinheiro':      inv.dinheiro,
            'semente':       inv.semente,
            'semente_esp':   inv.semente_esp,
            'muda':          inv.muda,
            'colheita':      inv.colheita,
            'colheita_esp':  inv.colheita_esp,
            'madeira':       inv.madeira,
            'peixe_comum':   inv.peixe_comum,
            'peixe_dourado': inv.peixe_dourado,
            'peixe_raro':    inv.peixe_raro,
            'semente_ativa': inv.semente_ativa,
            'dia':           hor.dia,
            'predios':       self.predios,
            'animais':       self.animais,
            'tem_vara':      self.tem_vara,
            'mapa_fazenda':  mapa_serial,
            'timer_plantas': tp_serial,
        }
        try:
            with open(CAMINHO_SAVE, 'w', encoding='utf-8') as arq:
                json.dump(dados, arq, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def carregar(self):
        if not os.path.isfile(CAMINHO_SAVE):
            return
        try:
            with open(CAMINHO_SAVE, encoding='utf-8') as arq:
                d = json.load(arq)
        except Exception:
            return

        inv = self.inventario
        inv.dinheiro      = int(d.get('dinheiro',      inv.dinheiro))
        inv.semente       = int(d.get('semente',       inv.semente))
        inv.semente_esp   = int(d.get('semente_esp',   inv.semente_esp))
        inv.muda          = int(d.get('muda',          inv.muda))
        inv.colheita      = int(d.get('colheita',      inv.colheita))
        inv.colheita_esp  = int(d.get('colheita_esp',  inv.colheita_esp))
        inv.madeira       = int(d.get('madeira',       inv.madeira))
        inv.peixe_comum   = int(d.get('peixe_comum',   inv.peixe_comum))
        inv.peixe_dourado = int(d.get('peixe_dourado', inv.peixe_dourado))
        inv.peixe_raro    = int(d.get('peixe_raro',    inv.peixe_raro))
        inv.semente_ativa = d.get('semente_ativa', inv.semente_ativa)

        self.horario.dia = int(d.get('dia', 1))

        if 'predios' in d:
            self.predios.update(d['predios'])
        if 'animais' in d:
            self.animais = list(d['animais'])

        self.tem_vara = bool(d.get('tem_vara', False))

        if 'mapa_fazenda' in d and d['mapa_fazenda'] is not None:
            self.mapa_fazenda = d['mapa_fazenda']

        if 'timer_plantas' in d:
            self.timer_plantas = {
                (int(k.split(',')[0]), int(k.split(',')[1])): int(v)
                for k, v in d['timer_plantas'].items()
            }
