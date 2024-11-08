#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import argparse
import etcd3
import utils.Utils as uitls
import tzcp.tbk.tbk_pb2 as tbkpb


class TBKApi:
    def __init__(self):
        self.MESSAGE_PREFIX = "/tbk/ps"
        self.PARAM_PREFIX = "/tbk/params"
        # self.param_data = {}
        # self.param_data_last = {}
        # self.param_tree = {}
        # self.param_is_change = False
        # self.message_data = {}
        # self.message_data_last = {}
        # self.message_is_change = False
        self.etcd = self._client()
        # self.update_param()
        # self.update_message()

    def _client(self):
        pkipath = os.path.join(os.path.expanduser("~"), ".tbk/etcdadm/pki")
        return etcd3.client(
            host="127.0.0.1",
            port=2379,
            ca_cert=os.path.join(pkipath, "ca.crt"),
            cert_key=os.path.join(pkipath, "etcdctl-etcd-client.key"),
            cert_cert=os.path.join(pkipath, "etcdctl-etcd-client.crt"),
        )

    def get_param(self, _prefix=None):
        # self.etcd = self.__client()
        prefix = self.PARAM_PREFIX + (_prefix if _prefix else "")
        raw_data = self.etcd.get_prefix(prefix)
        data = dict(
            [
                (r[1].key.decode('utf-8', errors='ignore')[12:], r[0].decode('utf-8', errors='ignore'))
                for r in raw_data
            ]
        )
        result = {}
        # 遍历原始字典并分类存储
        for key, value in data.items():
            base_key = key.rsplit("/", 1)[0]
            suffix = key.rsplit("/", 1)[1]
            if base_key not in result:
                result[base_key] = {"info": None, "type": None, "value": None}
            if suffix == "__i__":
                result[base_key]["info"] = value
            elif suffix == "__t__":
                result[base_key]["type"] = value
            elif suffix == "__v__":
                result[base_key]["value"] = value
        self.param_data = result
        self.param_tree = uitls.build_param_tree(result)
        return result

    def put_param(self, param, value):
        self.etcd.put(f"/tbk/params/{param}", value)

    def update_param(self):
        self.param_data_last = self.param_data
        self.get_param()
        if self.param_data_last != self.param_data:
            self.param_change_data = uitls.compare_dicts(
                self.param_data, self.param_data_last
            )
            self.param_is_change = True
        else:
            self.param_change_data = {"added": {}, "removed": {}, "modified": {}}
            self.param_is_change = False

    def get_message(self):
        processes = {}
        publishers = {}
        subscribers = {}
        res = self.etcd.get_prefix(self.MESSAGE_PREFIX)
        for r in res:
            key, value = r[1].key.decode(), r[0]
            keys = key[len(self.MESSAGE_PREFIX):].split("/")[1:]
            info = None
            if len(keys) == 1:
                info = tbkpb.State()
                info.ParseFromString(value)
                processes[info.uuid] = info
            elif len(keys) == 3:
                if keys[1] == "pubs":
                    info = tbkpb.Publisher()
                    info.ParseFromString(value)
                    publishers[info.uuid] = info
                elif keys[1] == "subs":
                    info = tbkpb.Subscriber()
                    info.ParseFromString(value)
                    subscribers[info.uuid] = info
            else:
                print("Error: key error:", key)
        res = {"ps": processes, "pubs": publishers, "subs": subscribers}
        self.message_data = res
        return res

    def update_message(self):
        self.message_data_last = self.message_data
        self.get_message()
        if self.message_data_last != self.message_data:
            self.message_change_data = uitls.compare_dicts(
                self.message_data, self.message_data_last
            )
            self.message_is_change = True
        else:
            self.message_change_data = {"added": {}, "removed": {}, "modified": {}}
            self.message_is_change = False
