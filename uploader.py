import os
import re
import urllib
import json
import base64
from flask import url_for
from datetime import datetime
from random import randrange
import logging
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


class UpLoader(object):
    stateMap = [  # 上传状态映射表，国际化用户需考虑此处数据的国际化
        "SUCCESS",  # 上传成功标记，在UEditor中内不可改变，否则flash判断会出错
        "文件大小超出 upload_max_filesize 限制",
        "文件大小超出 MAX_FILE_SIZE 限制",
        "文件未被完整上传",
        "没有文件被上传",
        "上传文件为空",
    ]

    state_error = {
        "ERROR_TMP_FILE": "临时文件错误",
        "ERROR_TMP_FILE_NOT_FOUND": "找不到临时文件",
        "ERROR_SIZE_EXCEED": "文件大小超出网站限制",
        "ERROR_TYPE_NOT_ALLOWED": "文件类型不允许",
        "ERROR_CREATE_DIR": "目录创建失败",
        "ERROR_DIR_NOT_WRITEABLE": "目录没有写权限",
        "ERROR_FILE_MOVE": "文件保存时出错",
        "ERROR_FILE_NOT_FOUND": "找不到上传文件",
        "ERROR_WRITE_CONTENT": "写入文件内容错误",
        "ERROR_UNKNOWN": "未知错误",
        "ERROR_DEAD_LINK": "链接不可用",
        "ERROR_HTTP_LINK": "链接不是http链接",
        "ERROR_HTTP_CONTENTTYPE": "链接contentType不正确"
    }

    def __init__(self, file_obj=None, upload_path=None, config=None, _type=None):
        self.file_obj = file_obj
        self.upload_path = upload_path
        self.config = config
        self._type = _type
        self.base_name = self.get_file_path()
        self.filename = ''

    def up_file(self):
        """
            保存上传的 图片，文件，视频
        """
        if self.check_size():
            _ext = self.check_file_type()
            if _ext:
                self.base_name = self.base_name + _ext
                base_name = os.path.abspath(self.upload_path + self.base_name)
                if not os.path.isdir(os.path.dirname(base_name)):
                    try:
                        os.makedirs(os.path.dirname(base_name))
                    except IOError as e:
                        logger.exception(e)
                        self.state_info = self.get_state_error('ERROR_CREATE_DIR')
                self.filename = os.path.basename(base_name)
                try:
                    print(base_name)
                    self.file_obj.save(base_name)
                    self.state_info = self.stateMap[0]
                except Exception as e:
                    logger.exception(e)
                    self.state_info = self.get_state_error('ERROR_FILE_MOVE')
            else:
                self.state_info = self.get_state_error('ERROR_TYPE_NOT_ALLOWED')
        else:
            self.state_info = self.get_state_error('ERROR_SIZE_EXCEED')

    def up_base64(self):
        """
            保存上传的涂鸦,处理base64编码的图片上传
        """
        img = base64.b64decode(self.file_obj)
        if len(img) <= self.config.get('maxSize'):
            base_name = os.path.abspath(self.upload_path + self.base_name)
            self.base_name = self.base_name + '.png'
            if not os.path.isdir(os.path.dirname(base_name)):
                try:
                    os.makedirs(os.path.dirname(base_name))
                except IOError as e:
                    logger.exception(e)
                    self.state_info = self.get_state_error('ERROR_CREATE_DIR')
            full_filename = base_name + '.png'
            try:
                with open(full_filename, 'wb') as fp:
                    fp.write(img)
                self.state_info = self.stateMap[0]
            except Exception as e:
                logger.exception(e)
                self.state_info = self.get_state_error('ERROR_FILE_MOVE')
        else:
            self.state_info = self.get_state_error('ERROR_SIZE_EXCEED')

    def save_remote(self):
        """
            保存远程上传图片 , 其他服务器的图片，可以不用存储
        """
        pass

    def check_size(self):
        size = self.file_obj.stream.read()  # 读完文件流，需要把指针设回起点
        self.file_obj.stream.seek(0, 0)
        length = len(size)
        print(length)
        if length > self.config.get('maxSize'):
            return False
        return True

    def check_file_type(self):
        """
            检测文件类型
        """
        file_name = secure_filename(self.file_obj.filename)
        if file_name:
            file_postfix = file_name.split('.')[1]
            file_extension = '.' + file_postfix.lower()
            if file_extension in self.config.get('allowFiles', None):
                return file_extension
        return False

    def get_file_path(self):
        """
            获取文件路径
        """
        filename_path = self.config.get('pathFormat', None)
        if filename_path:
            now = datetime.now()
            filename_path = filename_path.replace('{yyyy}{mm}{dd}',
                                                  str(now.year) + '-' + str(now.month) + '-' + str(now.day))
            filename_path = filename_path.replace('{time}', now.strftime('%H%M%S'))

            rand_re = r'\{rand\:(\d*)\}'
            _pattern = re.compile(rand_re, flags=re.I)
            ret_list = re.findall(_pattern, filename_path)
            if ret_list:
                num = int(ret_list[0])
                rand_nums = str(randrange(10 ** (num - 1), 10 ** num))
                _path = _pattern.sub(rand_nums, filename_path)
                return _path
        return None

    def get_state_error(self, err):
        """
            上传错误
        """
        return self.state_error.get(err, 'ERROR_UNKNOWN')

    def callback_info(self):
        """
        :return: 返回当前上传信息
        """
        return {
            "state": self.state_info,
            "url": url_for('static', filename=self.base_name[1:], _external=True),
            "title": self.filename,
            "original": self.filename,
        }
