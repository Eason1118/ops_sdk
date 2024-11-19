# OPS_SDK
## 项目结构说明
```
ops_sdk/
├── README.md                         
├── ops_sdk                    
│   ├── __init__.py            # 对外模块引用
│   ├── api                    # 第三方接口集合
│   │   ├── cmdb.py            # CMDB接口封装
│   │   ├── config.py          # 配置中心接口封装
│   │   ├── flow.py            # 任务调度接口封装
│   │   └── gmt.py             # GMT接口封装
│   ├── libs                   # 公共依赖
│   │   └── utils.py           # 公共模块
│   ├── service                # 提供服务的封装函数
│   │   └── ro.py              # ro相关服务数据的函数
│   ├── settings.py            # 全局配置，如默认的CODO，GMT请求地址
│   └── tests                  # 测试
│       └── ro_test.py         # ro业务函数测试
└── setup.py                   # 用于项目构建和分发
```
## build 
```shell script
[huanle@harilou-16-20 demo_python_package]$ python setup.py sdist
[huanle@harilou-16-20 demo_python_package]$ ll dist/
total 8
-rw-r--r-- 1 huanle huanle 2724 Apr 18 18:39 example_package-0.0.1.tar.gz # 上传即可
```
## install
```shell script
[huanle@harilou-16-20 demo_python_package]$ pip3 install -U ops_sdk -i https://pypi.huanle.com/simple
```
## 使用示例
```shell script
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/6/03 10:36
# @Author  : harilou
# @Describe: 将RO CMDB、配置中心数据同步GMT, 如果存在则跳过
import logging
import os
from ops_sdk import ROData, ROBindConf, get_env_file_connext

log_format = '%(asctime)s|%(levelname)s|%(message)s'
logging.basicConfig(format=log_format, datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)


def sync_gmt_data():
    gmt_auth = dict(user=os.getenv("GMT_API_CERD_USR"), passwd=os.getenv("GMT_API_CERD_PSW"))
    auth_key = get_env_file_connext(os.getenv("CODO_CMDB_API_KEY"))
    game_id = os.getenv("codo_game_id")
    biz_id = os.getenv("codo_biz_id")
    plat_code = os.getenv("codo_plat_code")
    project_code = os.getenv("codo_project_code")
    assert game_id, "地区ID不能为空"
    assert biz_id, "biz_id不能为空"
    assert plat_code, "环境code不能为空"
    assert project_code, "配置中心-项目前缀不能为空"
    assert auth_key, "auth_key不能为空"

    conf_tree_data = {
        "project_code": project_code
    }
    ro = ROData(codo_auth=auth_key, gmt_auth=gmt_auth, biz_id=biz_id, conf_tree_data=conf_tree_data, game_id=game_id,
                platform_code=plat_code)

    ro_bind_conf = ROBindConf(plat_code=plat_code, game_id=game_id, gmt_auth=gmt_auth)
    for item in ro.to_gmt_data():
        ro_bind_conf.run(data=item)
    return


if __name__ == '__main__':
    sync_gmt_data()

```