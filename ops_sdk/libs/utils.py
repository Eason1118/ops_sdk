#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/4/28 16:05
# @Author  : harilou
# @Describe:
import requests
import logging
import os


class Request:
    def __init__(self, url, method, headers=None, **kwargs):
        self.url = url
        self.method = method
        self.headers = headers
        self.session = requests.session()
        self.kwargs = kwargs

    def request_main(self):
        try:
            re_data = self.session.request(self.method, self.url, headers=self.headers, **self.kwargs)
        except Exception as e:
            raise Exception(f"请求失败：{e}")
        return re_data

    @staticmethod
    def init_codo_request_header(auth_key):
        return {"Sdk-Method": "zQtY4sw7sqYspVLrqV", "Cookie": f"auth_key={auth_key}"}


class CODOAuth:

    def __init__(self, auth_key=None):
        self.auth_key = os.getenv("CODO_API_KEY", auth_key)
        if self.auth_key is None or self.auth_key.strip() == "":
            raise Exception("auth not be none or empty")
        self.headers = Request.init_codo_request_header(self.auth_key)


class GMTAuth:

    def __init__(self, auth_data=None):
        user, passwd = auth_data.get('user'), auth_data.get('passwd')
        if user is None or user.strip() == "":
            raise Exception("GMT user not be none or empty")
        if passwd is None or passwd.strip() == "":
            raise Exception("GMT passwd not be none or empty")
        self.username = os.getenv("GMT_API_CERD_USR", user)
        self.password = os.getenv("GMT_API_CERD_PSW", passwd)


def get_env_file_connext(env_path):
    connext = None
    if env_path and os.path.exists(env_path):
        with open(env_path, "r") as f:
            connext = f.read().strip()
    else:
        logging.warning(f"Not find env_path:{env_path}")
    return connext
