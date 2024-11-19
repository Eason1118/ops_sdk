#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/4/28 16:58
# @Author  : harilou
# @Describe: 获取RO业务相关数据集
import yaml
import json
import copy
import logging
import os
from ops_sdk.api.config import ConfigCenterHandler
from ops_sdk.api.cmdb import CMDBDataHandler
from ops_sdk.api.gmt import GMTHeadler
from ops_sdk.settings import PROD_ENV_LIST


class RODataHeadle:

    def __init__(self, codo_auth: str,
                 gmt_auth: dict = None,
                 biz_id: str = None,
                 conf_tree_data: dict = dict(),
                 game_id: str = None,
                 platform_id: str = None,
                 platform_code: str = None):
        self.codo_auth = codo_auth
        self.biz_id = biz_id
        self.game_id = game_id
        self.gmt_api = GMTHeadler(self.game_id, gmt_auth)

        if platform_id is None and platform_code is None:
            raise Exception("platform_id and project_code is empty!")
        if platform_id is None and platform_code:
            self.platform_id = self.gmt_api.get_platform_id(platform_code)
        else:
            self.platform_id = platform_id

        # 配置中心对应树信息
        if conf_tree_data.get('project_code') is None:
            self.project_code = self.get_project_code(platform_code)
        else:
            self.project_code = conf_tree_data['project_code']
        self.env_name = conf_tree_data.get('env_name', platform_code)
        self.service = conf_tree_data.get('service', 'conf')
        self.filename = conf_tree_data.get('filename', 'conf.yml')

        self.asset_data = self.get_asset()
        self.conf_data = self.get_conf_yml()
        self.content = self.get_content()

    def get_project_code(self, code):
        code_list = code.split("_")
        if code.startswith("ro_cn_stress"):
            return "ro_hmt"
        if len(code_list) > 2:
            return "_".join(code_list[:2])
        elif "live" in code:
            return code.split("live")[0]
        else:
            raise Exception(f"错误的code格式:{code}; 正确格式：ro_<地区>_<环境>")

    def get_asset(self):
        handler = CMDBDataHandler(self.biz_id, self.env_name, auth_key=self.codo_auth)
        return handler.fetch_asset()

    def get_conf_yml(self):
        cc_handler = ConfigCenterHandler(env_name=self.env_name, project_code=self.project_code, service=self.service,
                                         filename=self.filename, auth_key=self.codo_auth)
        config = cc_handler.get_publish_config()
        return yaml.safe_load(config)

    def get_content(self):
        child_list = self.gmt_api.get_gmt_child_list(self.platform_id)
        server_name_list = self.gmt_api.get_gmt_server_name_list(self.platform_id)
        target_data = self.generate_target_data(self.conf_data, self.asset_data, child_list, server_name_list)
        return target_data

    # 生成process配置数据的函数
    def generate_process_data(self, region_id, module_name, asset_data, need_op, **kwargs):
        # 初始化内网IP和公网IP为空字符串
        inner_ip = ""
        outer_ip = ""
        if region_id == 100000:
            region_id = 'platform'
            module_name = module_name
        region_id = str(region_id)
        # 查找匹配的资产信息
        for asset in asset_data["data"]:
            if asset.get("region_name") == region_id and asset.get("module_name") == module_name:
                inner_ip = asset.get("inner_ip", inner_ip)
                outer_ip = asset.get("outer_ip", outer_ip)
                break

        # 构建process配置
        process_config = {
            "status": 1,
            "inner_ip": inner_ip,
            "outer_ip": outer_ip,
            "need_op": need_op
        }
        process_config.update(kwargs)
        return process_config


    # 只适用于模块下单主机的场景
    def get_asset_ip(self, asset_data, region_id, module_name=None):
        if region_id == 100000:
            region_id = 'platform'
            module_name = module_name
        # 如果测试环境不提供module_name，自动补充modulue_name
        else:
            if not module_name:
                if region_id == 'platform':
                    module_name = "platform"
                elif region_id > 9000:
                    module_name = 'cross'
                else:
                    module_name = 'vm0'
        region_id = str(region_id)
        for asset in asset_data["data"]:
            if module_name:
                if asset.get("region_name") == region_id and asset.get("module_name") == module_name:
                    inner_ip = asset.get("inner_ip", None)
                    outer_ip = asset.get("outer_ip", None)
                    return [inner_ip, outer_ip]
            else:
                if asset.get("region_name") == region_id:
                    inner_ip = asset.get("inner_ip", None)
                    outer_ip = asset.get("outer_ip", None)
                    return [inner_ip, outer_ip]
        raise Exception(f"CMDB未找到区服ID:{region_id}")

    def generate_target_data(self, conf_data, asset_data, child_list, server_name_list):
        # 初始化target数据结构
        target_data = {
            "platform": {
                "process": {},
                "inner_ip": "",
                "outer_ip": "",
                "code": self.env_name,
                "db": {}
            },
            "group": []
        }

        # 用字典来存储每个区域的数据，以便将相同区域的模块和数据库组合在一起
        region_data_dict = {}

        for cluster in conf_data["clusters"]:
            region_id = cluster["server_id"]
            if region_id != 100000:
                region_name = server_name_list.get(str(region_id), str(region_id))
            else:
                region_name = "platform"
            db_ip_override = cluster.get("db_ip_override", {})

            region_data = region_data_dict.get(region_id, {
                "id": region_id,
                "name": region_name,
                "process": {},
                "db": {},
                "inner_ip": "",
                "outer_ip": ""
            })

            for module in cluster.get("modules", []):
                module_name = module["name"]
                process_list = conf_data["module_defaults"][module_name]["processes"]
                inner_ip, outer_ip = self.get_asset_ip(asset_data, region_id, module_name)
                need_op = 1
                for process in process_list:
                    process_name = process.get("name")
                    _process = copy.deepcopy(process)
                    if "override" in module:
                        override = module.get("override")
                        if process_name in override:
                            _process.update(override.get(process_name))

                    process_data = self.generate_process_data(region_id, module_name, asset_data, need_op, **_process)
                    if process_name not in region_data["process"]:
                        region_data["process"][f"{process_name}"] = [process_data]
                    else:
                        region_data["process"][f"{process_name}"].append(process_data)  # 修改key的格式
                region_data["need_op"] = need_op
                region_data["inner_ip"] = inner_ip
                region_data["outer_ip"] = outer_ip
                # 确保redis配置应用于正确的模块和进程
                redis_config = module.get("redis", {})
                for process_name, redis_data in redis_config.items():
                    # 只有当process确实存在时，才添加redis配置
                    if process_name in region_data["process"]:
                        region_data["process"][process_name][0]["remoteIp"] = redis_data["host"]
                        region_data["process"][process_name][0]["remotePort"] = redis_data["port"]

            for db_config in cluster.get("db", []):
                db_name = db_config["name"]
                db_details = None
                # 如果 "config" 字段存在，尝试从 "databases" 获取相关配置
                if "config" in db_config:
                    db_details = conf_data["databases"].get(db_config["config"])

                # 如果 "config" 字段不存在，直接从 "databases" 获取相关配置
                else:
                    db_details = conf_data["databases"].get(db_name)

                if db_ip_override:
                    db_inner_ip = db_ip_override.get("inner_ip", "")
                    db_outer_ip = db_ip_override.get("outer_ip", "")
                else:
                    db_inner_ip, db_outer_ip = self.get_asset_ip(asset_data, region_id)
                db_data = {
                    "DBname": db_name,
                    "username": db_details.get("username", ""),
                    "password": db_details.get("password", ""),
                    "port": db_details.get("port", 3306),
                    "inner_ip": db_inner_ip,
                    "outer_ip": db_outer_ip,
                }
                region_data["db"][db_name] = [db_data]

            # 从gmt获取子服信息，然后放在db_child结构里面。
            if str(region_id) in child_list:
                if child_list[str(region_id)]:
                    region_data["db"]["db_child"] = child_list[str(region_id)]
            # 将platform的进程信息放入target的platform中
            if region_id == 100000:
                target_data["platform"]["name"] = region_name
                target_data["platform"]["id"] = region_id
                target_data["platform"]["process"].update(region_data["process"])
                target_data["platform"]["db"] = region_data["db"]
                # platform的server_id使用特殊的数字100000
                target_data["platform"]["inner_ip"], target_data["platform"]["outer_ip"] = self.get_asset_ip(asset_data, 100000,
                                                                                                        "platform")
            else:
                # 更新这个区域的数据
                region_data_dict[str(region_id)] = region_data

        # 将region_data_dict转换为列表并分配给target_data["group"]
        target_data["group"] = list(region_data_dict.values())

        return target_data


class GMTWriteJson:
    """将数据转为GMT可写入格式数据"""
    def __init__(self, data):
        self.content = data

    def add_db_conf(self, range_data, apd_data):
        for name, item in range_data.items():
            db_data = {
                "name": name,
                "gmt_conf": {
                    "port": item[0]["port"],
                    "extended_config": {
                        "username": item[0]["username"],
                        "db_host": item[0]["inner_ip"],
                        "password": item[0]["password"],
                        "DBname": item[0]["DBname"]
                    }
                }
            }
            apd_data.append(db_data)
        return apd_data

    def add_process_conf(self, range_data, apd_data):
        for name, item in range_data.items():
            info = item[0]
            process_data = {
                "name": name,
                "gmt_conf": {
                    "process_num": info.get("process_num", 1),
                    "port": info.get("port"),
                    "extended_config": {}
                }
            }
            if "extended_config" in info:
                process_data["gmt_conf"]["extended_config"] = json.loads(info["extended_config"])
            if "remoteIp" in info:
                process_data["gmt_conf"]["extended_config"]["remoteIp"] = info["remoteIp"]
            if "remotePort" in info:
                process_data["gmt_conf"]["extended_config"]["remotePort"] = info["remotePort"]

            for k, v in info.items():
                if k.startswith("expand_"):
                    process_data["gmt_conf"]["extended_config"][k] = v

            apd_data.append(process_data)
        return apd_data

    def to_json(self):
        platform = self.content["platform"]
        platform_data = {
            "name": platform["name"],
            "sg_id": platform["id"],
            "inner_ip": platform["inner_ip"],
            "outer_ip": self.content["platform"]["outer_ip"],
            "db": list(),
            "process": list()
        }
        self.add_db_conf(range_data=platform["db"], apd_data=platform_data['db'])
        self.add_process_conf(range_data=platform["process"], apd_data=platform_data['process'])
        sg_list = list()
        sg_list.append(platform_data)
        for item in self.content["group"]:
            gs_data = {
                "name": item["name"],
                "sg_id": item["id"],
                "inner_ip": item["inner_ip"],
                "outer_ip": item["outer_ip"],
                "db": list(),
                "process": list()
            }
            self.add_db_conf(range_data=item["db"], apd_data=gs_data['db'])
            self.add_process_conf(range_data=item["process"], apd_data=gs_data['process'])
            sg_list.append(gs_data)
        return sg_list


class ROBindConf(GMTHeadler):
    def __init__(self, plat_code, *args, **kwargs):
        self.plat_code = plat_code
        super(ROBindConf, self).__init__(*args, **kwargs)
        self.plat_id = self.get_platform_id(platform_code=self.plat_code)
        self.exist_procss_list = self.get_exist_procss_list()

    def fetch_process_id(self, proc_name):
        """获取进程的ID"""
        try:
            process_data = self.get_process()
            proces_id = [str(item["id"]) for item in process_data["data"] if item["name"] == proc_name]
            return str(proces_id[0])
        except:
            raise Exception(f"Not find proc_name:{proc_name}")

    def fetch_server_id(self, ser_id, inner_ip, outer_ip):
        """根据内网IP和外网IP找到对应ID，没有则创建"""
        server_list = self.get_server_list()
        server_id_list = [item['id'] for item in server_list['data'] if item["ip"] == inner_ip and item["outer_ip"]
                          == outer_ip]
        if len(server_id_list) == 0:
            logging.warning("GMT服务器列表没有匹配到！自动创建")
            name = f"{self.plat_code}-{ser_id}"
            params = dict(
                name=name,
                ip=inner_ip,
                outer_ip=outer_ip,
                description=name,
                ipv6=""
            )
            ret = self.create_server_list(params)
            server_id = ret['data']['id']
        else:
            server_id = server_id_list[0]
        return server_id

    def check_sg_exist(self, sg_name, sg_id):
        """校验区服是否存在"""
        plat_data = self.get_plat_data(platform_id=self.plat_id)
        gate_servers = plat_data['data']['gate_servers']
        if not gate_servers:
            raise Exception("请先创建大区！")
        status = False
        for item in gate_servers[0]["groups"]:
            if item["info"]["name"] == sg_name or item["info"]["outer_id"] == sg_id:
                status = True
        return status

    def get_sg_bind_id(self, sg_name, sg_id, inner_ip, outer_ip):
        """获取区服ID"""
        plat_data = self.get_plat_data(platform_id=self.plat_id)
        gate_servers = plat_data['data']['gate_servers']
        server_id = self.fetch_server_id(sg_id, inner_ip, outer_ip)
        if not gate_servers:
            logging.debug("没有大区，开始自动创建")
            big_area_params = dict(
                platform_id=self.plat_id,
                name=plat_data['data']['info']['name'],
                outer_id=2,
                status=0,
                server_id=server_id
            )
            ret = self.create_big_area(big_area_params)
            if ret['code'] != 200:
                logging.error(f"params:{big_area_params}; ret:{ret}")
                raise Exception(f"创建大区失败！")
            group_level_1_id = ret["data"]["id"]
        else:
            group_level_1_id = gate_servers[0]['info']['id']
            # 查询对应的区服ID
            for item in gate_servers[0]["groups"]:
                if item["info"]["name"] == sg_name or item["info"]["outer_id"] == sg_id:
                    return item["info"]["id"]
        # 没有区服，则新建
        add_group_params = dict(
            platform_id=self.plat_id,
            gateserver_id=group_level_1_id,
            name=sg_name,
            outer_id=sg_id,
            status=0,
            server_id=server_id
        )
        ret = self.create_group(add_group_params)
        if ret['code'] != 200:
            logging.error(f"params:{add_group_params}; ret:{ret}")
            raise Exception(f"创建区服:{sg_name}失败！")
        return ret["data"]["id"]

    def get_exist_procss_list(self):
        """获取已存在的进程信息； <process_name>-<server_id>-<bind_id>"""
        procss_list = list()

        plat_data = self.get_plat_data(platform_id=self.plat_id)
        if "bind_processes" in plat_data["data"] and plat_data["data"]["bind_processes"]:
            plat_bind_id = plat_data["data"]["info"]["id"]
            for item in plat_data["data"]["bind_processes"]:
                platform_procss = f"{item['process']['name']}-{item['server_id']}-{plat_bind_id}"
                procss_list.append(platform_procss)

        if "gate_servers" in plat_data["data"] and plat_data["data"]["gate_servers"]:
            for item in plat_data["data"]["gate_servers"][0]["groups"]:
                sg_bind_id = item["info"]["id"]
                for proc in item["bind_processes"]:
                    process_name = proc["process"]["name"]
                    sg_procss = f"{process_name}-{proc['server_id']}-{sg_bind_id}"
                    procss_list.append(sg_procss)
        return procss_list

    def run(self, data):
        """添加平台配置"""
        inner_ip, outer_ip, sg_id, sg_name = data["inner_ip"], data["outer_ip"], data["sg_id"], data["name"]
        if not outer_ip:
            outer_ip = inner_ip
        if sg_name == "platform":
            bind_id = self.plat_id
            bind_type = 1
        else:
            bind_id = self.get_sg_bind_id(sg_name, sg_id, inner_ip, outer_ip)
            bind_type = 3

        gmt_type_list = ["process", "db"]
        for gmt_type in gmt_type_list:
            if gmt_type not in data:
                continue
            for item in data[gmt_type]:
                name, conf = item['name'], item['gmt_conf']
                if 'extended_config' in conf and "db_host" in conf['extended_config']:
                    inner_ip = conf['extended_config'].pop("db_host")
                    outer_ip = inner_ip
                proces_id = self.fetch_process_id(name)
                server_id = self.fetch_server_id(sg_id, inner_ip, outer_ip)

                uuid = f"{name}-{server_id}-{bind_id}"
                if uuid in self.exist_procss_list:
                    logging.warning(f"{sg_name}-{name} 进程信息已绑定,无需重复绑定")
                    continue

                proces_params = dict(
                    bind_id=bind_id,
                    process_id=proces_id,
                    bind_type=bind_type,
                    status=1,
                    server_id=server_id,
                    process_num=1,
                    extended_config={"username": "", "password": ""}
                )
                if conf:
                    proces_params.update(conf)
                proces_params["extended_config"] = json.dumps(proces_params["extended_config"])
                logging.debug(proces_params)
                ret = self.bind_process(proces_params)
                if ret['code'] != 200:
                    logging.error(f"params:{proces_params}; \nret:{ret}")
                    raise Exception("绑定进程失败！")
        return


class ROData(RODataHeadle):

    def __init__(self, *args, **kwargs):
        super(ROData, self).__init__(*args, **kwargs)

    def all(self) -> dict:
        return self.content

    def to_gmt_data(self) -> list:
        return GMTWriteJson(self.content).to_json()


class ROConfig:

    def __init__(self, auth_key: str):
        self.auth_key = auth_key
        self.conf_tree = {
            "project_code": "ops",
            "env_name": "ro",
            "service": None,
            "filename": "conf.yaml"
        }

    def get_conf(self) -> str:
        conf_obj = ConfigCenterHandler(auth_key=self.auth_key, **self.conf_tree)
        return conf_obj.get_publish_config()

    def bastion(self) -> str:
        self.conf_tree.update({"service": "bastion"})
        return self.get_conf()

    def host(self) -> str:
        self.conf_tree.update({"service": "host"})
        return self.get_conf()

    def url(self) -> str:
        self.conf_tree.update({"service": "url"})
        return self.get_conf()

    def import_role_host(self) -> str:
        self.conf_tree.update({"service": "import_role_host"})
        return self.get_conf()

    def logbackup(self) -> str:
        self.conf_tree.update({"service": "logbackup"})
        return self.get_conf()

    @classmethod
    def prod_env_list(cls):
        return PROD_ENV_LIST


class ROInventory:

    def __init__(self, auth_key, content, plat_code):
        self.auth_key = auth_key
        self.content = content
        self.plat_code = plat_code

    def get_env_private_key(self, json_info):
        # 将配置文件中主机的ansible_ssh_private_key_file需要从环境变量中获取
        for env, info in json_info.items():
            if "ansible_ssh_private_key_file" in info:
                json_info[env]["ansible_ssh_private_key_file"] = os.getenv(info["ansible_ssh_private_key_file"], "")
            if "ansible_ssh_common_args" in info:
                ssh_args = json_info[env]["ansible_ssh_common_args"]
                if "!" in ssh_args:
                    env_accesse_key = ssh_args.split("!")[1]
                    access_valus = os.getenv(env_accesse_key, "")
                    json_info[env]["ansible_ssh_common_args"] = ssh_args.replace("!%s!" % env_accesse_key, access_valus)
        return

    def parse_config(self):
        ro_config = ROConfig(self.auth_key)
        bastion_info = yaml.safe_load(ro_config.bastion())
        self.get_env_private_key(bastion_info)
        host_info = yaml.safe_load(ro_config.host())
        self.get_env_private_key(host_info)
        return bastion_info, host_info

    def get_host_config(self, code_prefix, host_info):
        if code_prefix in host_info.keys():
            return host_info[code_prefix]
        return host_info["default"]

    def get_host_inventory(self, code_prefix, inner_ip, host_info, name):
        host = self.get_host_config(code_prefix, host_info)
        host["ansible_host"] = inner_ip
        host["name"] = name
        return host

    def hosts(self, sg_id_list):
        bastion_info, host_info = self.parse_config()
        inventory = {
            "all": [],
            "vm": [],
            "platform": [],
            "bastion": [],
            "cross": []
        }
        # 来源主机信息
        code = "_".join(self.plat_code.split("_")[:2])
        if code in bastion_info:
            bastion = bastion_info[code]
            inventory["all"].append(bastion)
            inventory["bastion"].append(bastion['name'])
        else:
            raise Exception(
                f"code:{code}, plat_code:{self.plat_code}, bastion_info not find! bastion_info:{bastion_info.keys()}")

        for item in self.content['group']:
            ser_id = str(item['id'])
            if ser_id not in sg_id_list:
                continue
            inner_ip = item['inner_ip']
            name = f"server-{ser_id}-{inner_ip}"
            vm_info = self.get_host_inventory(code, inner_ip, host_info, name)
            inventory["all"].append(copy.deepcopy(vm_info))
            if int(ser_id) < 9000:
                inventory["vm"].append(name)
            elif int(ser_id) > 9000 and int(ser_id) < 10000:
                inventory["cross"].append(name)
            else:
                raise Exception(f"ser_id: {ser_id}不规范!")

        if "platform" in sg_id_list:
            plat_data = self.content['platform']
            plat_srever_list = list(set([item[0]["inner_ip"] for item in plat_data['process'].values()]))
            for inner_ip in plat_srever_list:
                name = f"server-0-{inner_ip}"
                vm_info = self.get_host_inventory(code, inner_ip, host_info, name)
                inventory["all"].append(copy.deepcopy(vm_info))

        return inventory




