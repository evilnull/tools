#!/usr/bin/env python3
# coding:utf-8

import getopt
import os
import re
import sys
import threading
import time

import requests


class m3u8():
    def __init__(self, m3u8_file_path, base_url=''):
        self.__m3u8_file_path = m3u8_file_path
        self.__base_url = base_url
        self.__lock = threading.Lock()
        self.__thread_list = []
        self.__check()
        self.__save_dir_path = ''
        self.__thread_num = 10

    def __now(self):
        return time.strftime("%Y-%m-%d %H:%M:%S",   time.localtime())

    def __check(self):
        if not os.path.exists(self.__m3u8_file_path):
            print('[{0}] m3u8 file ({1}) does not exist'.format(self.__now(), self.__m3u8_file_path))
            sys.exit(1)
        if not os.path.isfile(self.__m3u8_file_path):
            print('[{0}] m3u8 file ({1}) is not file'.format(self.__now(), self.__m3u8_file_path))
            sys.exit(1)

    def __download_from_url_and_save_as_file(self, thread_name, url, save_file_path):
        print('[{0}] {1} start downloading {2}'.format(self.__now(), thread_name, url))
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'
        }
        request = requests.get(url, headers=headers)
        response = request.content
        with open(save_file_path, 'wb') as file:
            file.write(response)
        print('[{0}] {1} successful downloading of {2}, ans save as {3}'.format(self.__now(), thread_name, url, save_file_path))

    def __decode_m3u8_from_file(self):
        count = 0
        with open(self.__m3u8_file_path, 'r') as m3u8_file:
            for line in m3u8_file:
                line = line.strip()
                if line[0] != '#':
                    if re.match(r'(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]', line, re.I):
                        self.__base_url = ''
                    elif self.__base_url:
                        if self.__base_url[-1] != '/':
                            self.__base_url = self.__base_url +'/'
                    else:
                        print('m3u8 error, url invalid, base_url is needed')
                        sys.exit(1)
                        #raise Exception # url invalid
                    break
            m3u8_file.seek(0, 0)
            for line in m3u8_file:
                line = line.strip()
                if line[0] != '#':
                    count = count + 1
                    yield (self.__base_url + line, line.split('?')[0], count)

    def __target(self, thread_name):
        print('{} start'.format(thread_name))
        while True:
            self.__lock.acquire()
            try:
                url, path, count= next(self.__url_generator)
            except StopIteration:
                break
            finally:
                self.__lock.release()
            self.__download_from_url_and_save_as_file(thread_name, url, os.path.join(self.__save_dir_path, path))
        print('{} stop'.format(thread_name))

    def dowload(self, save_dir_path, thread_num=10):
        self.__save_dir_path = save_dir_path
        self.__thread_num = thread_num
        
        if not os.path.exists(self.__save_dir_path):
            print('[{0}] save dir ({1}) is not exist, will create it'.format(self.__now(), self.__save_dir_path))
            os.makedirs(self.__save_dir_path)
        if not os.path.isdir(self.__save_dir_path):
            print('[{0}] save dir ({1}) is not exist, will create it'.format(self.__now(), self.__save_dir_path))
            sys.exit(1)

        self.__url_generator = self.__decode_m3u8_from_file()
        for i in range(self.__thread_num):
            self.__thread_list.append(threading.Thread(target=self.__target, name='Thread-{}'.format(i), args=('Thread-{}'.format(i),)))
        for i in range(self.__thread_num):
            self.__thread_list[i].start()
        for i in range(self.__thread_num):
            self.__thread_list[i].join()
        #print('[{}] dowload successful'.format(self.__now()))

    def merge(self, save_merge_file_path):
        directory = os.path.split(os.path.realpath(save_dir_path))[0]
        if not os.path.exists(directory):
            print('[{0}] {1} does not exist, will create it'.format(self.__now(), directory))
            os.makedirs(directory)
        if not os.path.isdir(directory):
            print('[{0}] {1} is not directory'.format(self.__now(), directory))
            sys.exit(1)
        if os.path.exists(save_merge_file_path) and not os.path.isfile(save_merge_file_path):
            print('[{0}] {1} is not file'.format(self.__now(), save_merge_file_path))
            sys.exit(1)
        try:
            file = open(save_merge_file_path, 'wb')
            with open(self.__m3u8_file_path, 'r') as m3u8_file:
                for line in m3u8_file:
                    line = line.strip()
                    if line[0] != '#':
                        path = os.path.join(self.__save_dir_path, line.split('?')[0])
                        if not os.path.exists(path):
                            print('[{0}] {1} does not exist, program will exit'.format(self.__now(), path))
                            sys.exit(1)
                        temp = open(path, 'rb')
                        file.write(temp.read())
                        temp.close()
        except Exception as ex:
            print(ex.with_traceback)
        finally:
            file.close()

    def delete(self, save_dir_path=''):
        if not self.__save_dir_path and not save_dir_path:
            print('[{0}] delete path is needed'.format(self.__now()))
            sys.exit(1)
        if not save_dir_path:
            save_dir_path = self.__save_dir_path
        with open(self.__m3u8_file_path, 'r') as m3u8_file:
            for line in m3u8_file:
                line = line.strip()
                if line[0] != '#':
                    path = os.path.join(save_dir_path, line.split('?')[0])
                    if os.path.exists(path):
                        os.remove(path)
                        print('[{0}] successfully deleted {1}'.format(self.__now(), path))

def usage():
    print('m3u8 -f m3u8_file [-s save_dir] [-t thread_num] [-m save_merge_file] [-d delete_dir] [-u base_url]')

if __name__ == '__main__':
    m3u8_file_path = ''
    save_dir_path = ''
    thread_num = 10
    save_merge_file_path = ''
    delete_dir_path = ''
    base_url = ''
    try:
        opts, agrs = getopt.getopt(sys.argv[1:], 'hf:s:t:m:d:u:')
    except getopt.GetoptError:
        usage()
        sys.exit(1)
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit(1)
        elif opt == '-f':
            m3u8_file_path = arg
        elif opt == '-s':
            save_dir_path = arg
        elif opt == '-t':
            thread_num = int(arg)
        elif opt == '-m':
            save_merge_file_path = arg
        elif opt == '-d':
            delete_dir_path = arg
        elif opt == '-u':
            base_url = arg
    m = m3u8(m3u8_file_path, base_url)
    if save_dir_path:
        m.dowload(save_dir_path, thread_num)
    if save_merge_file_path:
        m.merge(save_merge_file_path)
    if delete_dir_path:
        m.delete(delete_dir_path)

