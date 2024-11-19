#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/1/24 10:50
# @Author  : harilou
# @Describe:
import logging
log_format = '%(asctime)s|%(levelname)s|%(message)s'
logging.basicConfig(format=log_format, datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

CODO_HOST = "https://tianmen.huanle.com"

GMT_HOST = "https://gameadmin.123u.com"

# RO 正式环境code
PROD_ENV_LIST = ["ro_nalive", "ro_kr_cbt", "ro_jplive", "ro_shuguang", "ro_hmtlive", "ro_sealive", "ro_lnalive"]
