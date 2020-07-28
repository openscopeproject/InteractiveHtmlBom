import sys


class ExitCodes():
    ERROR_PARSE = 3
    ERROR_FILE_NOT_FOUND = 4
    ERROR_NO_DISPLAY = 5


class ParsingException(Exception):
    pass


def exit_error(logger, code, err):
    logger.error(err)
    sys.exit(code)
