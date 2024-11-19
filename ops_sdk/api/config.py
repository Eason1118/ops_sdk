#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/4/28 17:01
# @Author  : harilou
# @Describe: 配置中心数据
from ops_sdk.libs.utils import Request, CODOAuth
from ops_sdk.settings import CODO_HOST


class ConfigCenterHandler(CODOAuth):
    """
    从配置中心获取数据库配置信息文件
    """
    def __init__(self, project_code=None, env_name=None, service=None, filename=None, **kwargs):
        self.env_name = env_name
        self.project_code = project_code
        self.service = service
        self.filename = filename
        super(ConfigCenterHandler, self).__init__(**kwargs)

    def get_publish_config(self):
        params = {
            'project_code': self.project_code,
            'environment': self.env_name,
            'service': self.service,
            'filename': self.filename
        }
        url = f"{CODO_HOST}/api/kerrigan/v1/conf/publish/config/"
        req = Request(url, "GET", params=params, headers=self.headers)
        res = req.request_main().json()
        if "data" not in res:
            raise Exception("get_publish_config: %s" % res)
        return res["data"].get(self.get_filename_key())

    def update_conf_file(self, content):
        url = f"{CODO_HOST}/api/kerrigan/v1/conf/publish/config/"
        params = {
            'project_code': self.project_code,
            'environment': self.env_name,
            'service': self.service,
            'filename': self.filename,
            'content': content
        }
        req = Request(url, "PUT", params=params, headers=self.headers)
        res = req.request_main()
        if res.status_code != 200:
            raise Exception(f"CfgApi.modify_conf_file:请求失败:{res.text}")
        response_data = res.json()
        if response_data.get("code") != 0:
            raise Exception("CfgApi.modify_conf_file:修改配置文件失败", response_data.get("msg"))
        return response_data.get("msg")

    def get_filename_key(self):
        return f'/{self.project_code}/{self.env_name}/{self.service}/{self.filename}'
