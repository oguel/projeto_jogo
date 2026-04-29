"""
pesca_estado.py / fishing_state.py — Minigame de pesca estilo Guitar Hero.

Como funciona:
  • 4 pistas (A/S/W/D) com notas caindo de cima para baixo
  • Acertar uma nota enche a barra de captura
  • Errar ou deixar expirar diminui a barra
  • O padrão se repete em loop até: barra = 0% (escapou) ou 100% (capturado)
  • Contagem regressiva de 3 segundos antes de iniciar
"""
import pygame
import random
import math

from src.states    import EstadoBase, FONTES
from src.constants import ACOES_PESCA, LABELS_PESCA, CORES_PESCA

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configurações do minigame
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Y_ZONA_ACERTO   = 490   # posição y da zona de acerto
MEIA_PISTA      = 28    # metade da largura de cada pista
RAIO_NOTA       = 22    # raio do círculo de cada nota
JANELA_PERFEITO = 65    # apertado — precisa de precisão
JANELA_BOM      = 130   # janela bom mais curta
DECAIMENTO      = 8.0   # barra drena rápido — não pode hesitar
GANHO_PERFEITO  = +14.0  # base; multiplicado pelo combo
GANHO_BOM       = +6.0
PENALIDADE_ERRO = -16.0  # punição severa por erro
PENALIDADE_MISS = -24.0  # miss é pior ainda
MAX_LOOPS       = 3      # apenas 3 chances


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Nota — representa um círculo caindo em uma pista
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Nota:
    __slots__ = ('pista', 'tempo_acerto', 'tempo_spawn', 'estado', 'y')

    def __init__(self, pista: int, tempo_acerto: float, tempo_queda: float):
        self.pista       = pista
        self.tempo_acerto = tempo_acerto
        self.tempo_spawn  = tempo_acerto - tempo_queda
        self.estado       = 'pendente'  # pendente | perfeito | bom | expirou
        self.y            = -RAIO_NOTA


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EstadoPesca — estado principal do minigame de pesca
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class EstadoPesca(EstadoBase):
    def __init__(self, dados_jogo):
        self.gd  = dados_jogo
        self.cfg = dados_jogo.configuracao

        # Contagem regressiva de 3 segundos
        self.inicio_ms   = pygame.time.get_ticks() + 3000
        self.fase        = 'contagem'   # 'contagem' | 'jogando' | 'resultado'
        self.contagem    = 3

        # Escolhe um tipo de peixe aleatório
        tipos            = list(self.cfg.padroes_pesca.keys())
        self.tipo_peixe  = random.choice(tipos)
        self.dados_peixe = self.cfg.padroes_pesca[self.tipo_peixe]

        # Gera notas iniciais
        self.notas       = self._gerar_notas(0.0)

        # Barra de captura (0–100, começa em 20)
        self.barra       = 20.0
        self.ultima_att  = self.inicio_ms
        self._loops      = 0

        # Combo: acertos perfeitos consecutivos multiplicam o ganho
        self._combo      = 0   # contador de perfeitos seguidos
        self._tick       = 0   # tick geral de animação

        # Partículas: [x, y, vx, vy, cor, raio, vida_ms, nasceu_ms]
        self._particulas: list = []

        # Feedback visual flutuante [texto, x, y, timestamp, cor]
        self.feedback    = []

        # Resultado final
        self.resultado        = None
        self.tempo_resultado  = 0

        # Posições x das pistas (calculadas no desenhar)
        self.x_pistas    = [200, 290, 380, 470]

    # ── Geração e reinício do padrão ─────────────────────────────
    def _gerar_notas(self, tempo_inicio: float) -> list:
        """Gera a lista de notas a partir do padrão do peixe atual.

        O offset de tempo_queda garante que a primeira nota (beat=0) comece
        exatamente no TOPO da tela quando o jogo iniciar (agora_ms=0),
        em vez de aparecer já na zona de acerto.
        """
        bpm         = self.dados_peixe['bpm']
        ms_por_beat = 60_000 / bpm
        tempo_queda = float(self.dados_peixe['queda_ms'])
        # offset = tempo_queda: a nota do beat=0 tem tempo_spawn=tempo_inicio,
        # ou seja, ela começa a cair exatamente quando o jogo inicia.
        offset = tempo_queda
        return [
            Nota(pista, tempo_inicio + offset + beat * ms_por_beat, tempo_queda)
            for (beat, pista) in self.dados_peixe['padrao']
        ]

    def _reiniciar_padrao(self, agora_ms: float):
        """Reinicia as notas. Se atingiu MAX_LOOPS, o peixe foge automaticamente."""
        self._loops += 1
        if self._loops >= MAX_LOOPS:
            self._definir_resultado('escapou')
            return
        ms_por_beat = 60_000 / self.dados_peixe['bpm']
        queda       = float(self.dados_peixe['queda_ms'])
        inicio_prox = agora_ms + queda + 400
        self.notas  = [
            Nota(pista, inicio_prox + beat * ms_por_beat, queda)
            for (beat, pista) in self.dados_peixe['padrao']
        ]

    # ── Processar teclas ─────────────────────────────────────────
    def processar_eventos(self, eventos: list):
        if self.fase == 'resultado':
            for evento in eventos:
                if evento.type == pygame.KEYDOWN:
                    return self._finalizar()
            return self

        if self.fase != 'jogando':
            return self

        agora_ms = pygame.time.get_ticks() - self.inicio_ms
        teclas   = self.cfg.teclas

        for evento in eventos:
            if evento.type != pygame.KEYDOWN:
                continue
            pista = self._tecla_para_pista(evento.key, teclas)
            if pista is not None:
                self._tentar_acertar(pista, agora_ms)

        return self

    def _tecla_para_pista(self, tecla: int, mapa: dict) -> int | None:
        """Converte uma tecla pressionada para índice de pista (0–3)."""
        for i, acao in enumerate(ACOES_PESCA):
            if tecla == mapa.get(acao):
                return i
        return None

    def _tentar_acertar(self, pista: int, agora_ms: float):
        """Verifica se o jogador acertou uma nota na pista correta."""
        melhor = min(
            (n for n in self.notas if n.estado == 'pendente' and n.pista == pista),
            key=lambda n: abs(agora_ms - n.tempo_acerto),
            default=None
        )
        x_pista   = self.x_pistas[pista]
        diferenca = abs(agora_ms - melhor.tempo_acerto) if melhor else JANELA_BOM + 1

        if melhor and diferenca < JANELA_BOM:
            if diferenca < JANELA_PERFEITO:
                self._combo   += 1
                multi          = min(3.0, 1.0 + (self._combo - 1) * 0.5)  # 1x→1.5x→2x→2.5x→3x
                ganho          = GANHO_PERFEITO * multi
                melhor.estado  = 'perfeito'
                self.barra    += ganho
                label = f'PERFEITO! x{multi:.1f}' if multi > 1 else 'PERFEITO!'
                self._adicionar_feedback(label, x_pista, (100, 255, 100))
                self._spawn_particulas(x_pista, Y_ZONA_ACERTO, CORES_PESCA[pista], 14)
            else:
                self._combo    = 0
                melhor.estado  = 'bom'
                self.barra    += GANHO_BOM
                self._adicionar_feedback('BOM!', x_pista, (255, 230, 80))
                self._spawn_particulas(x_pista, Y_ZONA_ACERTO, (255, 230, 80), 6)
        else:
            self._combo    = 0
            self.barra    += PENALIDADE_ERRO
            self._adicionar_feedback('ERROU!', x_pista, (255, 60, 60))

        self.barra = max(0.0, self.barra)

    def _spawn_particulas(self, x: int, y: int, cor: tuple, qtd: int):
        agora = pygame.time.get_ticks()
        for _ in range(qtd):
            ang   = random.uniform(0, math.pi * 2)
            spd   = random.uniform(2.5, 7.0)
            vida  = random.randint(350, 700)
            raio  = random.randint(3, 7)
            self._particulas.append([float(x), float(y),
                                      math.cos(ang) * spd, math.sin(ang) * spd,
                                      cor, raio, vida, agora])

    def _adicionar_feedback(self, texto: str, x: int, cor: tuple):
        self.feedback.append([texto, x, Y_ZONA_ACERTO - 50, pygame.time.get_ticks(), cor])

    # ── Atualização por frame ─────────────────────────────────────
    def atualizar(self):
        agora_real = pygame.time.get_ticks()
        agora_ms   = agora_real - self.inicio_ms

        # Contagem regressiva
        if self.fase == 'contagem':
            self.contagem = max(1, math.ceil((self.inicio_ms - agora_real) / 1000))
            if agora_real >= self.inicio_ms:
                self.fase      = 'jogando'
                self.ultima_att = agora_real
            return None

        # Resultado: fecha automaticamente após 3.5s
        if self.fase == 'resultado':
            if agora_real - self.tempo_resultado > 3500:
                return self._finalizar()
            return None

        # Verifica vitória ANTES do decaimento — evita que o decaimento consuma
        # o ganho do acerto antes da verificação no mesmo frame
        if self.barra >= 100:
            self._definir_resultado('capturado')
            return None

        # Decaimento passivo da barra
        delta         = (agora_real - self.ultima_att) / 1000.0
        self.ultima_att = agora_real
        self.barra    = max(0.0, min(100.0, self.barra - DECAIMENTO * delta))

        # Move as notas para baixo
        queda = float(self.dados_peixe['queda_ms'])
        for nota in self.notas:
            if nota.estado != 'pendente':
                continue
            passado = agora_ms - nota.tempo_spawn
            if passado < 0:
                nota.y = -RAIO_NOTA
                continue
            nota.y = -RAIO_NOTA + (passado / queda) * (Y_ZONA_ACERTO + RAIO_NOTA)
            if agora_ms > nota.tempo_acerto + JANELA_BOM:
                nota.estado   = 'expirou'
                self.barra   += PENALIDADE_MISS
                self.barra    = max(0.0, self.barra)

        # Atualiza partículas
        self._tick += 1
        vivas = []
        for p in self._particulas:
            idade = agora_real - p[7]
            if idade < p[6]:
                p[0] += p[2]
                p[1] += p[3]
                p[3] += 0.18   # gravidade
                p[2] *= 0.96   # fricção
                vivas.append(p)
        self._particulas = vivas

        # Remove feedback velho (> 900ms)
        self.feedback = [f for f in self.feedback
                         if agora_real - f[3] < 900]

        # Verifica fim
        todas_prontas = all(n.estado != 'pendente' for n in self.notas)
        if self.barra <= 0:
            self._definir_resultado('escapou')
        elif self.barra >= 100:
            self._definir_resultado('capturado')
        elif todas_prontas:
            self._reiniciar_padrao(agora_ms)

        return None

    def _definir_resultado(self, resultado: str):
        if self.resultado is None:
            self.resultado       = resultado
            self.fase            = 'resultado'
            self.tempo_resultado = pygame.time.get_ticks()

    def _finalizar(self):
        """Fecha o minigame e volta ao mapa."""
        if self.resultado == 'capturado':
            id_item  = self.dados_peixe.get('item_recompensa', 'peixe_comum')
            qtd      = self.dados_peixe.get('qtd_recompensa', 1)
            self.gd.inventario.adicionar(id_item, qtd)
        self.gd.ultimo_resultado = self.resultado

        if self.gd.ultimo_mapa == 'fazenda':
            from src.farm_state import EstadoFazenda
            return EstadoFazenda(self.gd)
        from src.town_state import EstadoCidade
        return EstadoCidade(self.gd)

    # ── Desenho ──────────────────────────────────────────────────
    def desenhar(self, tela: pygame.Surface):
        largura, altura = tela.get_size()

        # Calcula posições x das 4 pistas
        total_larg    = 4 * 80
        inicio_pistas = largura // 2 - total_larg // 2 + 40
        self.x_pistas = [inicio_pistas + i * 80 for i in range(4)]

        # Fundo com ondas animadas
        tick = self._tick
        for linha_y in range(altura):
            p    = linha_y / altura
            onda = math.sin(tick * 0.04 + linha_y * 0.015) * 6
            r    = int(max(0, min(255, 6  + p * 14 + onda * 0.3)))
            g    = int(max(0, min(255, 6  + p * 14 + onda * 0.3)))
            b    = int(max(0, min(255, 22 + p * 55 + onda)))
            pygame.draw.line(tela, (r, g, b), (0, linha_y), (largura, linha_y))

        fonte_g = FONTES.get('grande', pygame.font.SysFont('arial', 28, bold=True))
        fonte_n = FONTES.get('normal', pygame.font.SysFont('arial', 18))
        fonte_p = FONTES.get('pequena', pygame.font.SysFont('arial', 14))

        # ── Contagem regressiva ──────────────────────────────────
        if self.fase == 'contagem':
            pulso   = 1.0 + 0.3 * math.sin(pygame.time.get_ticks() * 0.01)
            tam     = int(80 * pulso)
            fonte_c = pygame.font.SysFont('arial', tam, bold=True)
            num     = fonte_c.render(str(self.contagem), True, self.dados_peixe['cor'])
            tela.blit(num, (largura // 2 - num.get_width() // 2,
                             altura  // 2 - num.get_height() // 2))
            nome = fonte_g.render(f'🎣  {self.dados_peixe["nome"]}!', True, self.dados_peixe['cor'])
            tela.blit(nome, (largura // 2 - nome.get_width() // 2, 28))
            return

        # Nome do peixe
        nome = fonte_g.render(f'🎣  {self.dados_peixe["nome"]}', True, self.dados_peixe['cor'])
        tela.blit(nome, (largura // 2 - nome.get_width() // 2, 8))

        # Barra de captura
        self._desenhar_barra(tela, largura, fonte_p)

        # Combo no topo direito
        if self._combo >= 2:
            cor_c  = (255, 255, 80) if self._combo < 4 else (255, 140, 30)
            multi  = min(3.0, 1.0 + (self._combo - 1) * 0.5)
            pulso  = 1.0 + 0.08 * math.sin(tick * 0.25)
            tam_c  = int(22 * pulso)
            fc     = pygame.font.SysFont('arial', tam_c, bold=True)
            tc     = fc.render(f'COMBO x{self._combo}  ({multi:.1f}x)', True, cor_c)
            tela.blit(tc, (largura - tc.get_width() - 10, 10))

        # Pistas e zonas de acerto
        for i in range(4):
            x_pista = self.x_pistas[i]
            cor     = CORES_PESCA[i]

            # Faixa com gradiente vertical
            faixa = pygame.Surface((MEIA_PISTA * 2, altura), pygame.SRCALPHA)
            faixa.fill((*cor, 14))
            tela.blit(faixa, (x_pista - MEIA_PISTA, 0))
            # Bordas das pistas (sem alpha — na tela direta)
            cor_dim = tuple(max(0, c // 3) for c in cor)
            pygame.draw.line(tela, cor_dim,
                             (x_pista - MEIA_PISTA, 0), (x_pista - MEIA_PISTA, altura), 1)
            pygame.draw.line(tela, cor_dim,
                             (x_pista + MEIA_PISTA, 0), (x_pista + MEIA_PISTA, altura), 1)

            # Zona de acerto com anel pulsante (sem alpha na tela)
            pulso_z = 1.0 + 0.06 * math.sin(tick * 0.2 + i)
            raio_z  = int((RAIO_NOTA + 10) * pulso_z)
            # Halo via surface SRCALPHA
            halo = pygame.Surface((raio_z * 2 + 12, raio_z * 2 + 12), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*cor, 50),
                               (raio_z + 6, raio_z + 6), raio_z + 4)
            tela.blit(halo, (x_pista - raio_z - 6, Y_ZONA_ACERTO - raio_z - 6))
            pygame.draw.circle(tela, cor, (x_pista, Y_ZONA_ACERTO), raio_z, 3)
            pygame.draw.circle(tela, (200, 200, 200), (x_pista, Y_ZONA_ACERTO), raio_z, 1)

            # Tecla (maior, com fundo)
            fonte_tecla = pygame.font.SysFont('arial', 18, bold=True)
            rotulo = fonte_tecla.render(LABELS_PESCA[i], True, cor)
            ty = Y_ZONA_ACERTO + RAIO_NOTA + 16
            bg = pygame.Surface((rotulo.get_width() + 8, rotulo.get_height() + 4), pygame.SRCALPHA)
            bg.fill((*cor, 35))
            tela.blit(bg,     (x_pista - bg.get_width() // 2, ty - 2))
            tela.blit(rotulo, (x_pista - rotulo.get_width() // 2, ty))

        # Notas descendo (com brilho duplo)
        for nota in self.notas:
            if nota.estado == 'pendente' and -RAIO_NOTA <= nota.y <= Y_ZONA_ACERTO + 60:
                x_pista = self.x_pistas[nota.pista]
                cor     = CORES_PESCA[nota.pista]
                ny      = int(nota.y)
                # Brilho externo via surface SRCALPHA
                brilho_n = pygame.Surface((RAIO_NOTA * 2 + 20, RAIO_NOTA * 2 + 20), pygame.SRCALPHA)
                pygame.draw.circle(brilho_n, (*cor, 55),
                                   (RAIO_NOTA + 10, RAIO_NOTA + 10), RAIO_NOTA + 8)
                tela.blit(brilho_n, (x_pista - RAIO_NOTA - 10, ny - RAIO_NOTA - 10))
                # Sombra
                pygame.draw.circle(tela, (0, 0, 0), (x_pista + 3, ny + 3), RAIO_NOTA)
                # Corpo
                pygame.draw.circle(tela, cor, (x_pista, ny), RAIO_NOTA)
                # Anel branco
                pygame.draw.circle(tela, (255, 255, 255), (x_pista, ny), RAIO_NOTA, 2)
            elif nota.estado in ('perfeito', 'bom'):
                x_pista    = self.x_pistas[nota.pista]
                cor_acerto = (100, 255, 100) if nota.estado == 'perfeito' else (255, 230, 80)
                # Halo via surface SRCALPHA
                halo_a = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.circle(halo_a, (*cor_acerto, 70), (40, 40), RAIO_NOTA + 18)
                tela.blit(halo_a, (x_pista - 40, Y_ZONA_ACERTO - 40))
                pygame.draw.circle(tela, cor_acerto, (x_pista, Y_ZONA_ACERTO), RAIO_NOTA + 14, 3)

        # Partículas
        agora_real_d = pygame.time.get_ticks()
        for p in self._particulas:
            idade = agora_real_d - p[7]
            pct   = 1.0 - idade / p[6]
            alfa  = int(255 * pct)
            raio  = max(1, int(p[5] * pct))
            surf_p = pygame.Surface((raio * 2 + 2, raio * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(surf_p, (*p[4], alfa), (raio + 1, raio + 1), raio)
            tela.blit(surf_p, (int(p[0]) - raio, int(p[1]) - raio))

        # Feedback visual flutuante
        for (texto, fx, fy, nasceu, cor) in self.feedback:
            idade  = pygame.time.get_ticks() - nasceu
            alfa   = max(0, 255 - int(idade / 900 * 255))
            subida = int(idade / 900 * 38)
            surf   = fonte_g.render(texto, True, cor)
            surf.set_alpha(alfa)
            tela.blit(surf, (fx - surf.get_width() // 2, fy - subida))

        # Tentativas restantes (alerta vermelho piscante no ultimo loop)
        loops_rest = MAX_LOOPS - self._loops
        if loops_rest <= 1:
            pisca = int(255 * abs(math.sin(tick * 0.15)))
            cor_alert = (pisca, 40, 40)
        else:
            cor_alert = (160, 160, 220)
        dica = fonte_p.render(f'Tentativas: {loops_rest}/{MAX_LOOPS}  |  Encha a barra!', True, cor_alert)
        tela.blit(dica, (largura - dica.get_width() - 10, 60))

        # Tela de resultado
        if self.fase == 'resultado':
            capturou = self.resultado == 'capturado'
            cor_res  = (80, 255, 120) if capturou else (255, 80, 80)
            msg_res  = '🐟 PEIXE CAPTURADO!' if capturou else '💨 O peixe escapou...'
            surf_res = pygame.font.SysFont('arial', 42, bold=True).render(msg_res, True, cor_res)
            brilho   = pygame.Surface((surf_res.get_width() + 40, surf_res.get_height() + 20), pygame.SRCALPHA)
            brilho.fill((*cor_res, 35))
            tela.blit(brilho,   (largura // 2 - brilho.get_width()   // 2, altura // 2 - brilho.get_height()   // 2))
            tela.blit(surf_res, (largura // 2 - surf_res.get_width() // 2, altura // 2 - surf_res.get_height() // 2))
            confirmar = fonte_n.render('Pressione qualquer tecla para continuar', True, (180, 180, 180))
            tela.blit(confirmar, (largura // 2 - confirmar.get_width() // 2, altura // 2 + 54))

    def _desenhar_barra(self, tela: pygame.Surface, largura: int, fonte):
        """Desenha a barra de captura no topo da tela."""
        larg_barra, alt_barra = 440, 28
        x_barra = largura // 2 - larg_barra // 2
        y_barra = 52

        # Pulso quando barra > 70% (animação de vitória próxima)
        if self.barra > 70:
            pulso = int(3 * abs(math.sin(self._tick * 0.18)))
            pygame.draw.rect(tela, (60, 180, 80),
                             (x_barra - pulso - 4, y_barra - pulso - 4,
                              larg_barra + (pulso + 4) * 2, alt_barra + (pulso + 4) * 2),
                             border_radius=8)

        # Fundo
        pygame.draw.rect(tela, (45, 45, 70),
                         (x_barra - 3, y_barra - 3, larg_barra + 6, alt_barra + 6), border_radius=8)
        pygame.draw.rect(tela, (18, 18, 38),
                         (x_barra, y_barra, larg_barra, alt_barra), border_radius=6)

        # Preenchimento com gradiente por camadas
        preench = int(larg_barra * min(self.barra, 100) / 100)
        if preench > 0:
            if self.barra > 60:
                cor1, cor2 = (60, 200, 60), (100, 255, 100)
            elif self.barra > 30:
                cor1, cor2 = (220, 170, 30), (255, 220, 60)
            else:
                cor1, cor2 = (200, 40, 40), (255, 80, 60)
            pygame.draw.rect(tela, cor1, (x_barra, y_barra, preench, alt_barra), border_radius=6)
            # Highlight superior
            pygame.draw.rect(tela, cor2,
                             (x_barra, y_barra, preench, alt_barra // 3), border_radius=6)

        # Marcadores em 25 / 50 / 75%
        for pct in (25, 50, 75):
            mx = x_barra + int(larg_barra * pct / 100)
            pygame.draw.line(tela, (120, 120, 160),
                             (mx, y_barra), (mx, y_barra + alt_barra), 1)

        # Borda
        pygame.draw.rect(tela, (80, 80, 120),
                         (x_barra, y_barra, larg_barra, alt_barra), 2, border_radius=6)

        # Texto centralizado
        label = f'⚡ {int(self.barra)}%' if self.barra <= 30 else f'{int(self.barra)}%'
        cor_t = (255, 100, 80) if self.barra <= 30 else (230, 230, 230)
        texto_barra = fonte.render(label, True, cor_t)
        tela.blit(texto_barra,
                  (x_barra + larg_barra // 2 - texto_barra.get_width() // 2,
                   y_barra + alt_barra // 2 - texto_barra.get_height() // 2))
