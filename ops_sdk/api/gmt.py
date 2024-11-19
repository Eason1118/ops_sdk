#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2023/12/21 16:53
# @Author  : harilou
# @Describe: 将RO的服务器和进程关系自动绑定GMT
from ops_sdk.settings import GMT_HOST
from ops_sdk.libs.utils import GMTAuth
import requests
import time
import hashlib
import logging
import json
import os
import copy


class GMTAPI(GMTAuth):
    def __init__(self, game_id, gmt_auth):
        super(GMTAPI, self).__init__(auth_data=gmt_auth)
        self.game_id = game_id
        self.gmt_host = os.getenv("GMT_API_HOST", GMT_HOST)
        self.headers = self._init_headers()

    def _init_headers(self):
        timestamp = str(int(time.time()))
        sign_org = timestamp + str(self.password)
        md5 = hashlib.md5()
        md5.update(sign_org.encode('utf-8'))
        sign = md5.hexdigest().upper()
        return {"Email": self.username, "Time": timestamp, "Sign": sign}

    def get_data_from_api(self, deploy_id):
        url = f"{self.gmt_host}/api/outer/jenkins/%s" % deploy_id
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            logging.error(
                "GMT API:%s, status code:%d, body:%s" % (url, response.status_code, response.content.decode('utf-8')))
            raise Exception('request GMT API failed')
        if response.json().get("code", -1) != 200:
            logging.error(f"GMT API Fail! error:{response.text}")
            raise Exception('request GMT API failed')
        return json.loads(response.content)["data"]["build_parameters"]

    def get_plat_data(self, platform_id):
        url = f"{self.gmt_host}/api/games/{self.game_id}/outer/platforms/{platform_id}/all-info"
        return requests.get(url, headers=self.headers).json()

    def get_plat_list(self):
        url = f"{self.gmt_host}/api/games/{self.game_id}/platforms?status=&open_page=0"
        return requests.get(url, headers=self.headers).json()

    def get_server_list(self):
        """获取服务器列表"""
        url = f"{self.gmt_host}/api/games/{self.game_id}/outer/servers?open_page=0"
        return requests.get(url, headers=self.headers).json()

    def create_server_list(self, params):
        """创建服务器列表"""
        url = f"{self.gmt_host}/api/games/{self.game_id}/outer/server"
        return requests.post(url, headers=self.headers, params=params).json()

    def del_server_list(self, ser_id):
        """删除服务器列表"""
        url = f"{self.gmt_host}/api/games/{self.game_id}/outer/servers/{ser_id}"
        return requests.delete(url, headers=self.headers).json()

    def get_process(self):
        """获取进程列表"""
        url = f"{self.gmt_host}/api/games/{self.game_id}/outer/processes?open_page=0"
        return requests.get(url, headers=self.headers).json()

    def bind_process(self, params):
        """批量绑定进程"""
        url = f"{self.gmt_host}/api/games/{self.game_id}/outer/bind-process"
        return requests.post(url, headers=self.headers, params=params).json()

    def update_process(self, proces_id, params):
        """批量绑定进程"""
        url = f"{self.gmt_host}/api/games/{self.game_id}/outer/bind-processes/{proces_id}"
        return requests.put(url, headers=self.headers, params=params).json()

    def del_process(self, proces_id):
        """批量绑定进程"""
        url = f"{self.gmt_host}/api/games/{self.game_id}/outer/bind-processes/{proces_id}"
        return requests.delete(url, headers=self.headers).json()

    def get_platforms(self):
        """获取平台列表"""
        url = f"{self.gmt_host}/api/games/{self.game_id}/outer/platforms"
        return requests.get(url, headers=self.headers).json()

    def create_group(self, params):
        """创建区服"""
        url = f"{self.gmt_host}/api/games/{self.game_id}/outer/group"
        return requests.post(url, headers=self.headers, params=params).json()

    def create_big_area(self, params):
        """创建大服"""
        url = f"{self.gmt_host}/api/games/{self.game_id}/outer/gateserver"
        return requests.post(url, headers=self.headers, params=params).json()

    def get_server_status(self, platform_id):
        params = {
            "platform_id": platform_id,
            "open_page": 0
        }
        url = f"{self.gmt_host}/api/games/{self.game_id}/ro/outer/group-list"
        return requests.get(url, headers=self.headers, params=params).json()

    def split_service(self, params):
        url = f"{self.gmt_host}/api/games/{self.game_id}/ro/outer/split-service"
        return requests.post(url, headers=self.headers, params=params).json()

    def combine_group_split(self, params):
        """拆服"""
        url = f"{self.gmt_host}/api/games/{self.game_id}/ro/outer/combine-group-split"
        return requests.post(url, headers=self.headers, params=params).json()

    def combine_group_callback(self, params):
        """合服回调"""
        url = f"{self.gmt_host}/api/games/{self.game_id}/ro/outer/combine-group-callback"
        return requests.post(url, headers=self.headers, params=params).json()

    def del_group(self, group_id):
        """删除区服"""
        url = f"{self.gmt_host}/api/games/{self.game_id}/outer/groups/{group_id}"
        return requests.delete(url, headers=self.headers).json()

    def update_group(self, group_id, data):
        """修改区服信息或者ID"""
        url = f"{self.gmt_host}/api/games/{self.game_id}/outer/groups/{group_id}"
        return requests.put(url, headers=self.headers, data=data).json()


class GMTHeadler(GMTAPI):

    def __init__(self, *args, **kwargs):
        super(GMTHeadler, self).__init__(*args, **kwargs)

    def get_platform_id(self, platform_code):
        platform_data = self.get_platforms().get("data")
        for i in platform_data:
            if platform_code == i.get("code"):
                return i.get("id")
        raise Exception(f"not find platform_code:{platform_code} to id")

    def get_gmt_child_list(self, platform_id):
        # 获取gmt中相关game_id的数据
        plat_data = self.get_plat_data(platform_id)
        # 获取所有大区的信息
        gate_server_data = plat_data.get('data').get("gate_servers")
        if not gate_server_data:
            return list()
        # 获取2大区的所有区服信息
        groups = gate_server_data[0].get("groups")
        child_list = {}
        for group in groups:
            group_out_id = group["info"]["outer_id"]
            group_bind_processes = group["bind_processes"]
            group_child_list = []
            for bind_process in group_bind_processes:
                if 'db_child' == bind_process["process"]["name"]:
                    db_child = copy.deepcopy(json.loads(bind_process["extended_config"]))
                    db_child["port"] = bind_process["port"]
                    db_child["status"] = bind_process["status"]
                    db_child["process_num"] = bind_process["process_num"]
                    db_child["inner_ip"] = bind_process["server"]["ip"]
                    db_child["outer_ip"] = bind_process["server"]["outer_ip"]
                    group_child_list.append(db_child)
            if group_out_id not in child_list.keys():
                child_list[str(group_out_id)] = group_child_list
            else:
                logging.error("服配置信息重复了")
        return child_list

    def get_gmt_server_name_list(self, platform_id):
        # 获取gmt中相关game_id的数据
        plat_data = self.get_plat_data(platform_id)
        # 获取所有大区的信息
        gate_server_data = plat_data.get('data').get("gate_servers")
        if not gate_server_data:
            return dict()
        # 获取2大区的所有区服信息
        groups = gate_server_data[0].get("groups")
        child_list = {}
        for group in groups:
            group_out_id = group["info"]["outer_id"]
            group_name = group["info"]["name"]
            if group_out_id not in child_list.keys():
                child_list[str(group_out_id)] = group_name
            else:
                logging.error("服配置信息重复了")
        return child_list
