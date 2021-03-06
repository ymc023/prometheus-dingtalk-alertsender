# prometheus-dingtalk-alertsender 

### prometheus-dingtalk-alertsender 

```
最开始使用https://github.com/timonwong/prometheus-webhook-dingtalk
这个dingtalk插件，结果修改自定义模板后，始终报404，无法正常发送信息
最后，只有放弃这个插件，自己写个prometheus-dingtalk-alertsender
```

### 依赖
```
1. python3 
2. requests ,flask, gevent
3. 得有钉钉机器人

```

### 告警模板
```
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
```

```
修改模板需要修改.py源文件，同时对入参代码进行修改。
```

### Dockerfile
```
附带了一份Dockerfile,方便使用alpine构建镜像
```

### 说明
* 已构建基于alpine的prometheus-dingtalk-alertsender镜像，传入参数即可使用
```
docker pull registry.cn-hangzhou.aliyuncs.com/ymc023/prometheus-dingtalk-alertsender:latest

docker run -d \
--name dingtalk-alertsender \
-v /var/log/alertsender.log:/var/log/alertsender.log \
-p 9999:80 \
registry.cn-hangzhou.aliyuncs.com/ymc023/prometheus-dingtalk-alertsender:latest \
/usr/bin/alertsender 80 \
https://oapi.dingtalk.com/robot/send?access_token=9485341072c2c20b5ce58eea8c138427b7b52b \
/var/log/alertsender.log

以上，在本机映射端口为9999,其url应为: http://localhost:9999/dingtalk/send
使用src中alertsender.test本机快速验证： bash alertsender.test http://localhost:9999/dingtalk/send
除本机之外访问，应将localhost替换为ip

```

* alertsender api : /dingtalk/send
* alertsender 需要3个参数: 端口，钉钉机器人url,日志路径.如下：
```
./alertsender.py 80  https://oapi.dingtalk.com/robot/send?access_token="1ce45992e706db8eea8c138427b7b52b82ca17"  /var/log/alertsender/alertsender.log
```
* 使用构建好的docker镜像时，其路径与名称为：/usr/bin/alertsender ,参数同上
* alertsender.test 可快速验证告警通道是否正常，使用方法如下：
```
bash alertsender.test 这里填写prometheus-dingtalk-alertsender启动的http路径 
如果在本机以80端口启动并运行测试，则为: bash alertsender.test http://localhost/dingtalk/send 

```
* 正常测试信息应该如下：

#### [K8S告警信息](#)
##### 触发时间: 2021-05-09 15:48:52
##### 发送时间: 2021-05-17 14:02:37
##### 触发状态: firing
-----
##### alertname: Watchdog
prometheus: monitoring/k8s
severity: none

-----
##### message: 这是一个验证告警通道是否正常的通知，应确保此告警始终开启并能正确接收。

-----
[详情](http://k8s:9090/graph?g0.expr=vector%281%29&g0.tab=1)



