import os


def get_parser_by_extension(file_name, config, logger):
    ext = os.path.splitext(file_name)[1]
    if ext == '.kicad_pcb':
        return get_kicad_parser(file_name, config, logger)
    elif ext == '.json':
        return get_easyeda_parser(file_name, config, logger)
    else:
        return None


def get_kicad_parser(file_name, config, logger, board=None):
    from .kicad import PcbnewParser
    return PcbnewParser(file_name, config, logger, board)


def get_easyeda_parser(file_name, config, logger):
    from .easyeda import EasyEdaParser
    return EasyEdaParser(file_name, config, logger)
