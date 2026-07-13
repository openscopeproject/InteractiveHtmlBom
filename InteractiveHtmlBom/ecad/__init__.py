import os


def get_parser_by_extension(file_name, config, logger):
    ext = os.path.splitext(file_name)[1]
    if ext == '.kicad_pcb':
        # Prefer the IPC API parser, but only when an API server context is
        # actually present (KICAD_API_SOCKET is set by a running KiCad or by
        # kicad-cli's server mode, and kipy picks it up automatically).
        # Without it we must not connect to some unrelated running KiCad and
        # parse its open board; we fall back to the legacy SWIG parser, which
        # is the only one that loads the board file straight from disk.
        if os.environ.get('KICAD_API_SOCKET'):
            try:
                return get_kicad_parser(file_name, config, logger)
            except Exception as e:
                logger.info("IPC API unavailable (%s), "
                            "falling back to SWIG parser." % e)
        return get_kicad_swig_parser(file_name, config, logger)
    elif ext == '.json':
        """.json file may be from EasyEDA or a generic json format"""
        import io
        import json
        with io.open(file_name, 'r', encoding='utf-8') as f:
            obj = json.load(f)
        if 'pcbdata' in obj:
            return get_generic_json_parser(file_name, config, logger)
        else:
            return get_easyeda_parser(file_name, config, logger)
    elif ext in ['.fbrd', '.brd']:
        return get_fusion_eagle_parser(file_name, config, logger)
    else:
        return None


def get_kicad_parser(file_name, config, logger, kicad=None, board=None):
    from .kicad import IpcApiParser
    return IpcApiParser(file_name, config, logger, kicad, board)


# Backwards compatible alias for the IPC parser.
get_kicad_ipc_parser = get_kicad_parser


def get_kicad_swig_parser(file_name, config, logger, board=None):
    from .kicad_swig import PcbnewParser
    return PcbnewParser(file_name, config, logger, board)


def get_easyeda_parser(file_name, config, logger):
    from .easyeda import EasyEdaParser
    return EasyEdaParser(file_name, config, logger)


def get_generic_json_parser(file_name, config, logger):
    from .genericjson import GenericJsonParser
    return GenericJsonParser(file_name, config, logger)


def get_fusion_eagle_parser(file_name, config, logger):
    from .fusion_eagle import FusionEagleParser
    return FusionEagleParser(file_name, config, logger)
