"""
dados_jogo.py / game_data.py — Classes principais dos dados do jogo.

  Configuracao  – teclas, volumes, padrões de pesca, tela cheia
  Inventario    – itens, dinheiro, semente ativa, HUD
  SistemaHorario – relógio do dia
  DadosJogo     – objeto global compartilhado entre todos os estados
"""
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configuracao — teclas, áudio, tela
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Configuracao:
    def __init__(self):
        self.teclas            = dict(TECLAS_PADRAO)
        self.volumes           = dict(VOLUMES_PADRAO)
        self.padroes_pesca     = dict(PADROES_PESCA_PADRAO)
        self.tela_cheia        = False
        self.mudanca_resolucao = False
        self.carregar()

    def salvar(self):
        """Salva as configurações atuais em config.json."""
        dados = {
            'teclas': {acao: tecla for acao, tecla in self.teclas.items()},
            'volumes': self.volumes,
            'tela_cheia': self.tela_cheia,
        }
        try:
            with open(CAMINHO_CONFIG, 'w', encoding='utf-8') as arq:
                json.dump(dados, arq, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def carregar(self):
        """Carrega as configurações salvas de config.json, se existir."""
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Inventario — tudo que o jogador possui
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
        self.semente_ativa    = ID_SEMENTE   # qual semente está selecionada

    # Nomes legíveis das sementes para o HUD
    _NOME_SEMENTE = {
        ID_SEMENTE:     'Semente',
        ID_SEMENTE_ESP: 'Especial',
        ID_MUDA:        'Muda',
    }

    def ciclar_semente(self):
        """Alterna para a próxima semente no ciclo."""
        idx = CICLO_SEMENTES.index(self.semente_ativa)
        self.semente_ativa = CICLO_SEMENTES[(idx + 1) % len(CICLO_SEMENTES)]

    def quantidade(self, id_item: str) -> int:
        """Retorna quantos exemplares do item o jogador possui."""
        nome_attr = id_item.replace('-', '_')
        return getattr(self, nome_attr, 0)

    def adicionar(self, id_item: str, qtd: int = 1):
        """Adiciona exemplares de um item ao inventário."""
        nome_attr = id_item.replace('-', '_')
        if hasattr(self, nome_attr):
            setattr(self, nome_attr, getattr(self, nome_attr) + qtd)

    def remover(self, id_item: str, qtd: int = 1):
        """Remove exemplares de um item (sem ir abaixo de zero)."""
        nome_attr = id_item.replace('-', '_')
        if hasattr(self, nome_attr):
            setattr(self, nome_attr, max(0, getattr(self, nome_attr) - qtd))

    def vender_tudo(self) -> int:
        """Vende todos os itens vendáveis e retorna o total ganho."""
        total = 0
        for id_item, preco in PRECOS_VENDA.items():
            qtd = self.quantidade(id_item)
            if qtd > 0:
                total += qtd * preco
                self.remover(id_item, qtd)
        self.dinheiro += total
        return total

    def desenhar_hud(self, tela: pygame.Surface, fonte_pequena, fonte_normal=None, dia: int = 1):
        """Desenha o HUD de dinheiro e semente ativa no canto esquerdo."""
        fonte_n = fonte_normal or fonte_pequena

        # Painel de dinheiro
        txt_din  = fonte_pequena.render(f'💰 ${self.dinheiro}', True, (255, 230, 80))
        box_din  = pygame.Surface((txt_din.get_width() + 12, 24), pygame.SRCALPHA)
        box_din.fill((18, 14, 4, 195))
        pygame.draw.rect(box_din, (180, 150, 40), box_din.get_rect(), 1, border_radius=5)
        tela.blit(box_din,  (4, 4))
        tela.blit(txt_din,  (10, 7))

        # Dia
        txt_dia  = fonte_pequena.render(f'📅 Dia {dia}', True, (200, 220, 255))
        box_dia  = pygame.Surface((txt_dia.get_width() + 12, 24), pygame.SRCALPHA)
        box_dia.fill((18, 14, 4, 195))
        pygame.draw.rect(box_dia, (80, 100, 160), box_dia.get_rect(), 1, border_radius=5)
        tela.blit(box_dia,  (4, 32))
        tela.blit(txt_dia,  (10, 35))

        # Painel de madeira
        txt_mad  = fonte_pequena.render(f'🪵 {self.madeira}', True, (200, 170, 110))
        box_mad  = pygame.Surface((txt_mad.get_width() + 12, 24), pygame.SRCALPHA)
        box_mad.fill((18, 14, 4, 195))
        pygame.draw.rect(box_mad, (120, 90, 40), box_mad.get_rect(), 1, border_radius=5)
        tela.blit(box_mad,  (4, 60))
        tela.blit(txt_mad,  (10, 63))

        # Semente ativa — canto inferior esquerdo (maior e mais destacada)
        _COR_BORDA_SEMENTE = {
            ID_SEMENTE:     (60, 200, 60),
            ID_SEMENTE_ESP: (180, 60, 220),
            ID_MUDA:        (50, 170, 90),
        }
        nome_sem = self._NOME_SEMENTE.get(self.semente_ativa, '?')
        qtd_sem  = self.quantidade(self.semente_ativa)
        cor_sem  = (180, 255, 140) if qtd_sem > 0 else (160, 100, 100)
        txt_sem  = fonte_n.render(f'🌱 {nome_sem}  x{qtd_sem}', True, cor_sem)
        alt_tela = tela.get_height()
        larg_box  = txt_sem.get_width() + 18
        alt_box   = 30
        box2     = pygame.Surface((larg_box, alt_box), pygame.SRCALPHA)
        box2.fill((4, 22, 4, 210))
        cor_borda = _COR_BORDA_SEMENTE.get(self.semente_ativa, (60, 130, 60))
        pygame.draw.rect(box2, cor_borda, box2.get_rect(), 2, border_radius=7)
        tela.blit(box2,    (4, alt_tela - alt_box - 6))
        tela.blit(txt_sem, (13, alt_tela - alt_box - 1))

    def desenhar_painel(self, tela: pygame.Surface, fontes: dict, tem_vara: bool):
        """Desenha o painel completo de inventário (tecla I)."""
        largura, altura = tela.get_size()
        larg_painel = 360
        alt_painel  = 440
        px = largura  // 2 - larg_painel // 2
        py = altura   // 2 - alt_painel  // 2

        fundo   = pygame.Surface((larg_painel, alt_painel), pygame.SRCALPHA)
        fundo.fill((10, 14, 28, 245))
        pygame.draw.rect(fundo, (70, 80, 150), fundo.get_rect(), 2, border_radius=14)
        tela.blit(fundo, (px, py))

        fonte_g = fontes.get('grande', pygame.font.SysFont('arial', 22, bold=True))
        fonte_n = fontes.get('normal', pygame.font.SysFont('arial', 16))
        fonte_p = fontes.get('pequena', pygame.font.SysFont('arial', 13))

        titulo = fonte_g.render('📦 Inventário', True, (255, 235, 100))
        tela.blit(titulo, (px + larg_painel // 2 - titulo.get_width() // 2, py + 12))
        pygame.draw.line(tela, (60, 70, 140), (px + 12, py + 44), (px + larg_painel - 12, py + 44), 1)

        # Lista de itens
        itens = [
            (f'💰 Dinheiro',           f'${self.dinheiro}'),
            (f'🌱 Semente',             str(self.semente)),
            (f'✨ Semente Especial',    str(self.semente_esp)),
            (f'🌳 Muda de Árvore',     str(self.muda)),
            (f'🌾 Colheita',            str(self.colheita)),
            (f'💎 Colheita Especial',   str(self.colheita_esp)),
            (f'🪵 Madeira',             str(self.madeira)),
            (f'🐟 Peixe Comum',         str(self.peixe_comum)),
            (f'🌟 Peixe Dourado',       str(self.peixe_dourado)),
            (f'💜 Peixe Raro',          str(self.peixe_raro)),
            (f'🎣 Vara de Pesca',       '✅ Sim' if tem_vara else '❌ Não'),
        ]
        for indice, (rotulo, valor) in enumerate(itens):
            linha_y = py + 56 + indice * 32
            cor_label = (200, 200, 230)
            cor_valor = (255, 240, 140) if indice == 0 else (180, 230, 180)
            tela.blit(fonte_n.render(rotulo, True, cor_label), (px + 18, linha_y))
            surf_val  = fonte_n.render(valor, True, cor_valor)
            tela.blit(surf_val, (px + larg_painel - surf_val.get_width() - 18, linha_y))

        dica = fonte_p.render('[ I ] ou [ ESC ] para fechar', True, (80, 80, 110))
        tela.blit(dica, (px + larg_painel // 2 - dica.get_width() // 2, py + alt_painel - 22))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SistemaHorario — relógio interno do dia
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class SistemaHorario:
    def __init__(self):
        self._hora_real_inicio = pygame.time.get_ticks()
        self.hora              = HORA_INICIO
        self.minuto            = 0
        self.dia               = 1
        self.notificado_cansado = False

    def hora_atual(self) -> tuple[str, int, int]:
        """Retorna (string_hora, hora_int, minuto_int)."""
        ms_passados = pygame.time.get_ticks() - self._hora_real_inicio
        ticks       = ms_passados // (SEGUNDOS_POR_TICK * 1000)
        total_min   = HORA_INICIO * 60 + ticks * MINUTOS_POR_TICK
        hora        = (total_min // 60) % 24
        minuto      = total_min % 60
        return f'{hora:02d}:{minuto:02d}', hora, minuto

    def eh_meia_noite(self) -> bool:
        """Verifica se chegou à hora de dormir forçado."""
        _, hora, _ = self.hora_atual()
        return hora >= HORA_FIM

    def hora_cansado(self) -> bool:
        """Verifica se o jogador está ficando cansado (1h antes do fim)."""
        _, hora, _ = self.hora_atual()
        return hora >= HORA_FIM - 1

    def nivel_escuridao(self) -> float:
        """Retorna nível de escuridão entre 0.0 (dia) e 1.0 (meia-noite)."""
        _, hora, _ = self.hora_atual()
        if hora < 18:
            return 0.0
        return min(1.0, (hora - 18) / 6)

    def reiniciar_dia(self):
        """Avança para o próximo dia e reinicia o relógio."""
        self.dia               += 1
        self.notificado_cansado = False
        self._hora_real_inicio  = pygame.time.get_ticks()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DadosJogo — contentor global compartilhado entre estados
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class DadosJogo:
    def __init__(self):
        self.configuracao   = Configuracao()
        self.inventario     = Inventario()
        self.horario        = SistemaHorario()

        # Mapa da fazenda (inicializado no EstadoFazenda)
        self.mapa_fazenda   = None
        self.timer_plantas  = {}     # (col, lin): timestamp em ms

        # Estado dos prédios
        self.predios = {
            ESTABULO_QUEBRADO:   ESTABULO_QUEBRADO,
            GALINHEIRO_QUEBRADO: GALINHEIRO_QUEBRADO,
        }

        # Animais (lista de dicionários)
        self.animais = []

        # Jogador (instância de Jogador)
        self.jogador = None

        # Flags e mensagens
        self.msg_cansado        = False
        self.timer_msg_cansado  = 0
        self.dormiu_voluntario  = False

        # Pesca
        self.tem_vara           = False
        self.ultimo_resultado   = None   # 'capturado' | 'escapou' | None

        # Navegação entre mapas
        self.ultimo_mapa        = 'fazenda'   # 'fazenda' | 'cidade'
