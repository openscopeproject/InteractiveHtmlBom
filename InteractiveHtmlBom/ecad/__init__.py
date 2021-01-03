import os


def get_parser_by_extension(file_name, config, logger):
    ext = os.path.splitext(file_name)[1]
    if ext == '.kicad_pcb':
        return get_kicad_parser(file_name, config, logger)
    elif ext == '.json':
        """.json file may be from EasyEDA or Eagle -
        look for '_source' attribute in the file to disambiguate"""
        import io
        import json
        with io.open(file_name, 'r') as f:
            obj = json.load(f)
        if '_source' in obj and obj['_source'] == 'eagle':
            return get_eagle_parser(file_name, config, logger)
        else:
            return get_easyeda_parser(file_name, config, logger)
    else:
        return None


def get_kicad_parser(file_name, config, logger, board=None):
    from .kicad import PcbnewParser
    return PcbnewParser(file_name, config, logger, board)


def get_easyeda_parser(file_name, config, logger):
    from .easyeda import EasyEdaParser
    return EasyEdaParser(file_name, config, logger)


def get_eagle_parser(file_name, config, logger):
    from .eagle import EagleParser
    return EagleParser(file_name, config, logger)
