#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/5/20 11:59
# @Author  : harilou
# @Describe: 任务平台
from ops_sdk.libs.utils import Request, CODOAuth
from ops_sdk.settings import CODO_HOST


class Flow(CODOAuth):
    def __init__(self, host_name=CODO_HOST, **kwargs):
        self.host_name = host_name
        super(Flow, self).__init__(**kwargs)

    def endpoint(self, url_path):
        return f"{self.host_name}/{url_path}"

    def create_flow(self, data):
        url = self.endpoint('api/job/v1/flow/accept/create/')
        req = Request(url=url, method='POST', data=data, headers=self.headers)
        return req.request_main()
