"""
jogo.py — Ponto de entrada do Farm Game.

Resolução fixa: 800×600.
Suporte a tela cheia/janela via Configuracao.
ESC em qualquer estado abre EstadoConfiguracoes.
"""
import pygame
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

pygame.init()
pygame.mixer.init()

from src          import assets as RECURSOS
from src.game_data import DadosJogo
from src.states    import EstadoTitulo, inicializar_fontes
from src.constants import FPS

RESOLUCAO = (800, 600)

_dados  = DadosJogo()
_flags  = pygame.FULLSCREEN if _dados.configuracao.tela_cheia else 0
TELA    = pygame.display.set_mode(RESOLUCAO, _flags)
pygame.display.set_caption('Fazenda  —  Vida no Campo')

inicializar_fontes()
RECURSOS.criar_pastas()

RELOGIO = pygame.time.Clock()


def main():
    global TELA

    dados  = _dados
    estado = EstadoTitulo(dados)

    while True:
        eventos = pygame.event.get()

        for ev in eventos:
            if ev.type == pygame.QUIT:
                dados.configuracao.salvar()
                pygame.quit()
                sys.exit()

        # Processar eventos → pode retornar novo estado
        novo = estado.processar_eventos(eventos)
        if novo is not estado:
            estado = novo
            continue

        # Atualizar → pode retornar novo estado
        resultado = estado.atualizar()
        if resultado is not None:
            estado = resultado
            continue

        # Aplicar mudança de resolução/tela cheia se pendente
        if dados.configuracao.mudanca_resolucao:
            dados.configuracao.mudanca_resolucao = False
            flags  = pygame.FULLSCREEN if dados.configuracao.tela_cheia else 0
            TELA   = pygame.display.set_mode(RESOLUCAO, flags)
            RECURSOS.limpar_cache()
            inicializar_fontes()

        # Desenhar
        estado.desenhar(TELA)
        pygame.display.flip()
        RELOGIO.tick(FPS)


if __name__ == '__main__':
    main()