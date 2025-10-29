import os


def get_parser_by_extension(file_name, config, logger):
    ext = os.path.splitext(file_name)[1]
    if ext == '.kicad_pcb':
        return get_kicad_parser(file_name, config, logger)
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


def get_kicad_parser(file_name, config, logger, board=None):
    from .kicad import PcbnewParser
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
