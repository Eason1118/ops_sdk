#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2023/5/30 17:51
# @Author  : harilou
# @Describe:
from ops_sdk.libs.utils import Request, CODOAuth
from ops_sdk.settings import CODO_HOST


class CMDBDataHandler(CODOAuth):
    def __init__(self, biz_id, env_name, host_name=CODO_HOST, **kwargs):
        self.biz_id = biz_id
        self.env_name = env_name
        self.host_name = host_name
        super(CMDBDataHandler, self).__init__(**kwargs)

    def endpoint(self, url_path):
        return f"{self.host_name}/{url_path}"

    def fetch_tree(self):
        params = {
            "biz_id": self.biz_id,
            "env_name": self.env_name,
            "asset_type": "server",
            "page_size": 10000,
            "page_number": 1
        }
        url = self.endpoint('api/cmdb/api/v2/cmdb/tree/')
        req = Request(url=url, method='GET', params=params, headers=self.headers)
        res = req.request_main()
        return res.json()

    def fetch_asset(self):
        params = {
            "biz_id": self.biz_id,
            "env_name": self.env_name,
            "asset_type": "server",
            "page_size": 10000,
            "page_number": 1
        }
        url = self.endpoint('api/cmdb/api/v2/cmdb/tree/asset/')
        req = Request(url=url, method='GET', params=params, headers=self.headers)
        res = req.request_main()
        return res.json()


class DBData(CODOAuth):
    def __init__(self, host_name=CODO_HOST, **kwargs):
        self.host_name = host_name
        super(DBData, self).__init__(**kwargs)

    def endpoint(self, url_path):
        return f"{self.host_name}/{url_path}"

    def get_db_all(self):
        params = {
            "page_number": 1,
            "page_size": 10000,
            "search_filter": "is_normal",
            "order_by": "",
            "order": "ascend"
        }
        url = self.endpoint('api/cmdb/api/v2/cmdb/mysql/')
        req = Request(url=url, method='GET', params=params, headers=self.headers)
        res = req.request_main()
        return res.json()