"""Script ligero para validar imports e invocar una acción de escaneo de prueba.

No arranca la GUI. Usa un logger simple que imprime en consola.
"""
from pprint import pprint

def logger(level, msg):
    print(f"[{level}] {msg}")


def main():
    logger('INFO', 'Import sanity: cargando módulos core...')
    try:
        from src.core import scanner, installer, config_manager
    except Exception:
        try:
            from core import scanner, installer, config_manager
        except Exception as e:
            logger('ERROR', f"Importación fallida: {e}")
            raise

    logger('INFO', 'Módulos importados correctamente. Leyendo configuración por defecto...')
    cfg = config_manager.load_config()
    pprint(cfg)

    logger('INFO', 'Ejecutando scan_games() (puede tardar y usar registro de Windows)...')
    try:
        games = scanner.scan_games(logger, custom_folders=cfg.get('custom_game_folders', []))
        logger('INFO', f"Escaneo retornó {len(games)} entradas (mostrando hasta 10)...")
        for g in games[:10]:
            pprint(g)
    except Exception as e:
        logger('ERROR', f"scan_games() falló: {e}")

    logger('OK', 'Import-sanity completado.')


if __name__ == '__main__':
    main()
