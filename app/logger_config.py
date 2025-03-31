import logging

def setup_logger():
    logger = logging.getLogger("flask_recommendation")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = True  # 터미널로 전달되도록 설정

    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
