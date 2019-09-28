# Author: Carl Cheung

import logging
import os
from logging.handlers import TimedRotatingFileHandler

"""
%(name)s Logger的名字
%(levelno)s 数字形式的日志级别
%(levelname)s 文本形式的日志级别
%(pathname)s 调用日志输出函数的模块的完整路径名，可能没有
%(filename)s 调用日志输出函数的模块的文件名
%(module)s 调用日志输出函数的模块名
%(funcName)s 调用日志输出函数的函数名
%(lineno)d 调用日志输出函数的语句所在的代码行
%(created)f 当前时间，用UNIX标准的表示时间的浮 点数表示
%(relativeCreated)d 输出日志信息时的，自Logger创建以 来的毫秒数
%(asctime)s 字符串形式的当前时间。默认格式是 “2003-07-08 16:49:45,896”。逗号后面的是毫秒
%(thread)d 线程ID。可能没有
%(threadName)s 线程名。可能没有
%(process)d 进程ID。可能没有
%(message)s用户输出的消息
"""


def log_init(log_path, module_name, verbose=False):
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)

    log_fmt = '[%(asctime)s]\t-\t%(filename)s\t-\t%(funcName)s\t-\t%(lineno)d\t-\t[%(levelname)s]: %(message)s'
    formatter = logging.Formatter(log_fmt)

    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    log_file_handler = TimedRotatingFileHandler(filename=log_path + "/{}".format(module_name), when="midnight",
                                                interval=1, backupCount=7, encoding='utf8')
    log_file_handler.suffix = '%Y%m%d.log'
    log_file_handler.setLevel(logging.INFO)
    log_file_handler.setFormatter(formatter)
    log.addHandler(log_file_handler)

    if verbose:
        print_handler = logging.StreamHandler()
        print_handler.setLevel(logging.INFO)

        log_fmt = '[%(asctime)s]\t-\t[%(levelname)s]: %(message)s'
        formatter = logging.Formatter(log_fmt)
        print_handler.setFormatter(formatter)

        log.addHandler(print_handler)

    return log


if __name__ == '__main__':
    log_init('log/', 'test')
