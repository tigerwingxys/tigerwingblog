#!/usr/bin/env python3
#
# Copyright 2019 Tigerwing(tigerwingxys@qq.com)
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# this file created at 2019.8.27
# 没有想好此文件如何使用，后续扩展
#
# 2019.11.23初步想法，将此表封装为所有数据库表的动态存取基类，定义下述属性：
#    Table  表名
#    FromList 取值列表，默认*
#    ValueList
#    ConditionList
#    Method: insert, update, delete
#    此类根据上述信息组装SQL语句，访问数据库，并返回结果
#    可提供可视化工具对表进行定制，然后提供一系列接口供访问

class BaseTable:
    def __init__(self):
        self.cached = False

    def get_cache_obj(self, obj_id):
        if self.cached is True:
            return None
        return None

    def flush_cache_obj(self, obj_id):
        pass
