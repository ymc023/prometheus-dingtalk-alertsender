#!/usr/bin/env python
# coding: utf-8

# Version: 0.1
# Author: ymc023
# Mail:
# Platform:
# Date: 2021年05月12日 星期三 10时41分29秒

from gevent import monkey
monkey.patch_all()

from flask import Flask, request, jsonify
from requests import Session
import logging
from queue import Queue
from json import dumps
from datetime import datetime, timedelta
import sys
from concurrent.futures import ThreadPoolExecutor
from gevent.pywsgi import WSGIServer
import socket


# 钉钉机器人api
DINGDING_REPORT_URL = ""
# 日志路径
LOG_PATH = "/var/log/alertsender.log"


# 告警模板
MSGFMT = """
#### [K8S告警信息](#)
##### 触发时间: {}
##### 发送时间: {}
##### 触发状态: {}
-----
##### {}
-----
##### {}
-----
{}
"""


# Log
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
log_handler = logging.FileHandler(LOG_PATH)
log_handler.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)
app = Flask(__name__)
msg_q = Queue()
executor = ThreadPoolExecutor(10)


@app.route('/dingtalk/send',
           methods=['POST'], endpoint='DingTalkPost')
def DingTalkPost():
    if request.get_data():
        content = request.data
        content = content.decode("utf-8")
        content = eval(content)
        logger.info("alert triger:%s" % content)

        try:
            alerts = content['alerts']
            DataClean(alerts)
        except Exception as e:
            logger.error("get map key alerts error:%s" % e)
            return(jsonify({"status": "fail", "message": "fail", "code": 500}), 500)
        executor.submit(DingSender)
        return "200"


def DingSender():
    for i in range(msg_q.qsize()):
        req = Session()
        datas = msg_q.get_nowait()
        try:
            req_data = req.post(DINGDING_REPORT_URL, data=datas, headers={
                "Content-Type": "application/json; charset=UTF-8"})
            if req_data.status_code != 200:
                logger.error("dingding send alert info error,code !=200")
            else:
                logger.info("dingding send alert info ok.")
        except Exception as e:
            logger.error("dingding send alert info fail:%s" % e)


def DataClean(alerts):
    try:
        for i in alerts:
            labels = ""
            annotations = ""
            status = i['status']
            # 针对kube-promethus自带的规则，去掉这个url
            try:
                del(i['annotations']['runbook_url'])
            except Exception:
                pass
            # 取出labels与annotations中所有数据
            for k, v in i['labels'].items():
                labels += "%s: %s\n" % (k, v)
            for k, v in i['annotations'].items():
                annotations += "%s: %s\n" % (k, v)

            # coreos kube-prometheus部署,传过来的时间为UTC,将其转化为+8的时间
            # 如果时区是正确的，则不转换，直接使用传过来的startsAt时间即可
            raw_time = i['startsAt'].split("T")
            raw_time1 = raw_time[1].split(".")
            utc_time = "%s %s" % (raw_time[0], raw_time1[0])
            alert_time = (
                datetime.strptime(
                    utc_time,
                    '%Y-%m-%d %H:%M:%S') +
                timedelta(
                    hours=8)).strftime("%Y-%m-%d %H:%M:%S")
            send_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 替换数据中的url为自己对外暴露的地址
            url = i['generatorURL'].replace(
                'prometheus-k8s-0:9090',
                'prometheus.***.com')
            msg = MSGFMT.format(
                alert_time,
                send_time,
                status,
                labels,
                annotations,
                "[详情](%s)" %
                url)
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "k8s Alert",
                    "text": msg
                },
                "at": {"isAtAll": "false"}
            }
            data = dumps(data)
            msg_q.put_nowait(data)
            logger.info("%s" % msg)

    except Exception as e:
        logger.error("data clean error:%s" % e)


def GetHostIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 0))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("invalid args.\n")
        print('Example: ./alertsender.py 9999  https://oapi.dingtalk.com/robot/send?access_token="1CDK..KKDK"  /var/log/alertsender.log')
        sys.exit(1)
    else:
        if sys.argv[1].isdigit():
            port = int(sys.argv[1])
            DINGDING_REPORT_URL = sys.argv[2]
            LOG_PATH = sys.argv[3]
            print("Set Port: %s,Set url: %s,Set log path: %s" % (port,
                                                                 DINGDING_REPORT_URL, LOG_PATH))
        else:
            print("invalid args.")
            print('Example: ./alertsender.py 9999  https://oapi.dingtalk.com/robot/send?access_token="1CDK..KKDK" /var/log/alertsender.log')
            sys.exit(1)

    try:
        http_server = WSGIServer(('0.0.0.0', int(port)), app)
        print("Start service with %s now...\n" % port)
        print("Access addr:  http://%s:%s/dingtalk/send \n" % (GetHostIp(), port))
        http_server.serve_forever()
    except KeyboardInterrupt:
        sys.exit()
