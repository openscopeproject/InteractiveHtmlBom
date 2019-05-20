def get_kicad_parser(file_name, logger, board):
    from .kicad import PcbnewParser
    return PcbnewParser(file_name, logger, board)
