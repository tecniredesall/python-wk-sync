import logging

def get_logger(name, level=logging.DEBUG) -> logging.Logger:
    FORMAT = "[%(levelname)s  %(name)s %(module)s:%(lineno)s - %(funcName)s() - %(asctime)s]\n\t %(message)s \n"
    TIME_FORMAT = "%d.%m.%Y %I:%M:%S %p"

    FILENAME = './logs/api.log'

    logging.basicConfig(format=FORMAT, datefmt=TIME_FORMAT, level=level,
    filename=FILENAME
    )

    logger = logging.getLogger(name)
    return logger