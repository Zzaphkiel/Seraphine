import os
import logging
import traceback
from logging.handlers import RotatingFileHandler
from datetime import datetime

from app.common.config import cfg


class CustomRotatingFileHandler(RotatingFileHandler):
    """
    使日志分片名称不再放到后缀中

    RotatingFileHandler: aaa.log.1
    CustomRotatingFileHandler: aaa_1.log
    """

    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self._get_new_file_name(i)
                dfn = self._get_new_file_name(i + 1)
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self._get_new_file_name(1)
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)
        if not self.delay:
            self.stream = self._open()

    def _get_new_file_name(self, index):
        """
        Generate a new file name with the index inserted before the extension.
        """
        base, ext = os.path.splitext(self.baseFilename)
        return f"{base}_{index}{ext}"


class Logger:
    def __init__(self, name, console_output=False):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(cfg.get(cfg.logLevel))

        log_directory = os.path.join(os.getcwd(), 'log')
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        log_file = self._get_log_file()
        file_handler = CustomRotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=20)
        formatter = logging.Formatter('%(asctime)s - [%(TAG)s] %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def _get_log_file(self):
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = f"{self.name}_{today}_%s.log" % logging.getLevelName(logging.DEBUG)
        log_path = os.path.join('log', log_file)
        return log_path

    def log(self, level, message, tag=None):
        extra = {'TAG': tag} if tag else {}
        self.logger.log(level, message, extra=extra)

    def debug(self, message, tag=None):
        self.log(logging.DEBUG, message, tag)

    def info(self, message, tag=None):
        self.log(logging.INFO, message, tag)

    def warning(self, message, tag=None):
        self.log(logging.WARNING, message, tag)

    def error(self, message, tag=None):
        self.log(logging.ERROR, message, tag)

    def exception(self, message, exce, tag=None):
        self.error(f"{message}: {self.get_traceback_string(exce)}", tag)

    def critical(self, message, tag=None):
        self.log(logging.CRITICAL, message, tag)

    def get_traceback_string(self, exception):
        # 获取异常的调用堆栈信息的字符串形式
        traceback_list = traceback.format_exception(type(exception), exception, exception.__traceback__)
        traceback_str = ''.join(traceback_list)
        return traceback_str


logger = Logger("Seraphine")


if __name__ == "__main__":
    # 示例：开启控制台输出
    log = Logger("Seraphine", console_output=True)

    log.debug("This is a debug message.")
    log.info("This is an info message.")
    log.warning("This is a warning message.")
    log.error("This is an error message.")
    log.critical("This is a critical message.")
