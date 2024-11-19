#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/4/29 10:36
# @Author  : harilou
# @Describe:
import logging
import os
import json
from ops_sdk import ROConfig, ROData, ROBindConf, ROInventory
from ops_sdk.api.gmt import GMTAPI

log_format = '%(asctime)s|%(levelname)s|%(message)s'
logging.basicConfig(format=log_format, datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)


def sample_sync_gmt_data():
    # 将RO CMDB、配置中心数据同步GMT
    gmt_auth = dict(user=os.getenv("GMT_API_CERD_USR"), passwd=os.getenv("GMT_API_CERD_PSW"))
    auth_key = os.getenv("CODO_FLOW_AUTH")
    game_id = 66
    plat_code = "ro_sea_totg_pre"
    biz_id = 508
    ser_id = "2"
    ro = ROData(codo_auth=auth_key, gmt_auth=gmt_auth, biz_id=biz_id, game_id=game_id,
                platform_code=plat_code)

    ro_bind_conf = ROBindConf(plat_code=plat_code, game_id=game_id, gmt_auth=gmt_auth)
    for item in ro.to_gmt_data():
        if str(item['sg_id']) == ser_id:
        #     logging.info(f"item: {json.dumps(item)}")
            ro_bind_conf.run(data=item)
    return


def get_db_child(group_id):
    gmt_auth = dict(user=os.getenv("GMT_API_CERD_USR"), passwd=os.getenv("GMT_API_CERD_PSW"))
    auth_key = os.getenv("CODO_FLOW_AUTH")
    game_id = 53
    plat_code = "ro_hmt_combine"
    conf_tree_data = {
        "project_code": "ro_hmt"
    }
    biz_id = 503
    ro = ROData(codo_auth=auth_key, gmt_auth=gmt_auth, biz_id=biz_id, conf_tree_data=conf_tree_data, game_id=game_id,
                platform_code=plat_code)

    for group in ro.content['group']:
        if str(group['id']) == str(group_id) and "db_child" in group['db']:
            print(group['db']['db_child'])
            return group['db']['db_child']
    return list()


def get_db_all():
    from ops_sdk.api.cmdb import DBData
    auth_key = os.getenv("CODO_FLOW_AUTH")
    api = DBData(auth_key=auth_key)
    data = api.get_db_all()
    print(data)


def get_ro_data():
    gmt_auth = dict(user=os.getenv("GMT_API_CERD_USR"), passwd=os.getenv("GMT_API_CERD_PSW"))
    auth_key = os.getenv("CODO_FLOW_AUTH")
    game_id = 66
    plat_code = "ro_sea_combine"
    biz_id = 508
    ro = ROData(codo_auth=auth_key, gmt_auth=gmt_auth, biz_id=biz_id, game_id=game_id, platform_code=plat_code)
    print(json.dumps(ro.content))
    return


def update_group_id():
    gmt_auth = dict(user=os.getenv("GMT_API_CERD_USR"), passwd=os.getenv("GMT_API_CERD_PSW"))
    gmt_api = GMTAPI(game_id=66,gmt_auth=gmt_auth)
    data = {"outer_id": "19"}
    ret = gmt_api.update_group(group_id="1926", data=data)
    print(ret)


if __name__ == '__main__':
    sample_sync_gmt_data()











