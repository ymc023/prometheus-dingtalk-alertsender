FROM registry.cn-hangzhou.aliyuncs.com/ymc023/pyinstaller-alpine:python3.7.10-pyinstaller  as alertsender_bin
ADD ./src/alertsender.py  /tmp/

RUN mkdir -p /root/.config/pip/ \
    && echo -e "[global]\nindex-url = http://mirrors.aliyun.com/pypi/simple\n[install]\ntrusted-host=mirrors.aliyun.com" >$HOME/.config/pip/pip.conf \
    && sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories \
    && apk add file make \
    && pip3 install --upgrade pip wheel \
    && pip3 install gevent flask requests \
    && cd /tmp \
    && pyinstaller -F alertsender.py



FROM alpine:3.11

MAINTAINER ymc023@163.com

ENV LANG=zh_CN.UTF-8 LC_ALL=zh_CN.UTF-8 VERSION=0.1 PS1='[\u@\w]$'

COPY --from=alertsender_bin /tmp/dist/alertsender  /usr/bin/

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories  \
    && apk add tzdata bash   \
    && mkdir -p /var/log/alertsender/  \
    && touch /var/log/alertsender/alertsender.log  \
    && chmod +x /usr/bin/alertsender  \
    && cp -rf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
CMD ["/usr/bin/alertsender" ,"修改成自己的dingding机器人地址","/var/log/alertsender/alertsender.log"]

