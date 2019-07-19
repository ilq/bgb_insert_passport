import logging
import os
import sys
import json
import csv
import urllib.parse
import urllib.request

# в конфиге храним логин/пароль от bgbilling'а и имя файла csv
CONFIG_FILE = 'config_example.JSON'

curdir = os.path.abspath(os.path.dirname(sys.argv[0]))

logging.basicConfig(
    format='%(levelname)-8s [%(asctime)s] %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H-%M-%S',
    filename='%s/bgbilling_entry_passport.log' % (curdir)
)

def read_configuration(config_file):
    with open(config_file) as f:
        config = json.load(f)
    return config

def get_passport_data(config_csv):
    with open(config_csv['filename']) as f:
        passports_data = csv.reader(f, delimiter=config_csv['delimiter'])
        for row in passports_data:
            yield row

def replace_line(line):
    """ Форматируем строку
    из: "1111 111111 Подразделение такое-то города такого-то 01.01.1111"
    в:  "1111_111111_Подразделение такое-то города такого-то_01.01.1111"
    """
    line = line.split()
    if line[0].isdigit():
        result = '%s_%s_%s' % (line[0], line[1], ' '.join(line[2:-1]))
    else:
        result = '%s' % (' '.join(line[:-1]))
    if line[-1].split('.')[-1].isdigit():
        result += '_%s' % line[-1]
    else:
        result += ' %s' % line[-1]
    result += '\n'
    return result


def insert_passport(config_bgbilling, cid, passport_string):
    params = {
        'user': config_bgbilling['user'],
        'pswd': config_bgbilling['pswd'],
        'pid': '371',
        'id': cid,
        'value': replace_line(passport_string),
        'cid': cid,
        }
    query = 'http://10.254.230.2:8080/bgbilling/executer?module=contract&action=UpdateParameterType1&' + urllib.parse.urlencode(params)
    logging.debug(query)
    with urllib.request.urlopen(query) as response:
        logging.debug(response.read())
    

def main():
    config = read_configuration(CONFIG_FILE)
    # Проверяем обязательные настройки
    if 'csv' not in config:
        logging.info('"csv" not set in %s' % CONFIG_FILE)
        sys.exit()
    if 'bgbilling' not in config:
        logging.info('"bgbilling" not set in %s' % CONFIG_FILE)
        sys.exit()
    # переустанавливаем уровень логгирования, если в конфиге задано:
    log_level = config.get('log_level', None)
    if log_level:
        logger = logging.getLogger()
        logger.setLevel(log_level)
    # создаем считыватель csv (генератор)
    passports_data = get_passport_data(config['csv'])
    # пропускаем заголовок, если в настройках установлено в True
    if config.get('has_header', None):
        passports_data.__next__()
    # в цикле проходим по данным из csv
    for row in passports_data:
        logging.info('|'.join(row))
        insert_passport(config['bgbilling'], *row)


if __name__ == "__main__":
    main()