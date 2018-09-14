from flask import Flask, render_template, url_for, make_response, request
import json
import os
import traceback
import re

from .uploader import UpLoader

app = Flask(__name__)

basedir = os.path.dirname(__file__)


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/upload/', methods=['GET', 'POST'])
def upload():
    """UEditor文件上传接口
        config 配置文件
        result 返回结果
        """
    result = {}
    action = request.args.get('action', None)
    with open(os.path.join(basedir, 'static', 'ueditor', 'python', 'config.json'), encoding='utf8') as f:
        t = f.read()
        try:
            CONFIG = json.loads(re.sub(r'\/\*.*\*\/', '', t))
        except Exception as e:
            traceback.print_exc(e)
            CONFIG = {}
    if action == 'config':
        result = CONFIG

    if request.method == 'POST':
        if action in ('uploadimage', 'uploadfile', 'uploadvideo'):
            # 图片、文件、视频上传
            if action == 'uploadimage':
                fieldName = CONFIG.get('imageFieldName', None)
                config = {
                    "pathFormat": CONFIG['imagePathFormat'],
                    "maxSize": CONFIG['imageMaxSize'],
                    "allowFiles": CONFIG['imageAllowFiles']
                }
            elif action == 'uploadvideo':
                fieldName = CONFIG.get('videoFieldName', None)
                config = {
                    "pathFormat": CONFIG['videoPathFormat'],
                    "maxSize": CONFIG['videoMaxSize'],
                    "allowFiles": CONFIG['videoAllowFiles']
                }
            else:
                fieldName = CONFIG.get('fileFieldName', None)
                config = {
                    "pathFormat": CONFIG['filePathFormat'],
                    "maxSize": CONFIG['fileMaxSize'],
                    "allowFiles": CONFIG['fileAllowFiles']
                }

            if fieldName in request.files:
                file = request.files[fieldName]
                uploader = UpLoader(file_obj=file, config=config, upload_path=os.path.join(basedir, 'static'))
                uploader.up_file()
                result = uploader.callback_info()
            else:
                result['state'] = '上传接口出错'

        elif action == 'uploadscrawl':
            # 涂鸦上传
            fieldName = CONFIG.get('scrawlFieldName')
            config = {
                "pathFormat": CONFIG.get('scrawlPathFormat'),
                "maxSize": CONFIG.get('scrawlMaxSize'),
                "allowFiles": CONFIG.get('scrawlAllowFiles'),
            }
            if fieldName in request.form:
                file = request.form[fieldName]
                uploader = UpLoader(file_obj=file, config=config,
                                    upload_path=os.path.join(basedir, 'static'), _type='base64')
                uploader.up_base64()
                result = uploader.callback_info()
            else:
                result['state'] = '上传接口出错'

    result = json.dumps(result)
    res = make_response(result)
    res.headers['Access-Control-Allow-Origin'] = '*'
    res.headers['Access-Control-Allow-Headers'] = 'X-Requested-With,X_Requested_With'
    return res


if __name__ == '__main__':
    app.run()
