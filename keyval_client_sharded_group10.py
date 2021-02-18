from __future__ import print_function
import argparse
import keyval_pb2
import keyval_pb2_grpc
import grpc
import logging
import re
import sys
import time

args = []

def parseArgs():
    global args
    parser = argparse.ArgumentParser(description="Key-value store server.")
    parser.add_argument("--write_timeout", default="0",
                        help=" The delay in seconds that is added to the Write RPC handling in the server, i.e., before the Write RPC is handled on the server side.")
    args = parser.parse_args()
    print('args', args)
    return args

def save_to_disk(res, op):
    with open("tmp/foo.txt", "a") as myfile:
        myfile.write(op + ' result:\n')
        myfile.write(str(res) + '\n')
        myfile.write('-------------------------------------------------------------------\n')
    return    

def Read(stub, obj):
    try:
        req = keyval_pb2.ReadRequest(key=obj['key'])
        res = stub.Read(req)

        save_to_disk(res, 'Read')
        print("Read result:\n")
        print(res,'\n')
        print('-------------------------------------------------------------------\n')
    except grpc.RpcError as exception:
        print(exception)
    return
        

def Write(stub, obj, timeout=60):
    try:
        res  = stub.Write(keyval_pb2.WriteRequest(key=obj['key'],value=obj['value'],current_version=obj['current_version']), timeout=timeout)
        save_to_disk(res, 'Write')
        print("Write result:\n")
        print(res, '\n')
        print('-------------------------------------------------------------------\n')
    except grpc.RpcError as exception:
        print(exception)
    return
    

def List(stub):
    try:
        res = stub.List(keyval_pb2.ListRequest())
        save_to_disk(res, 'List')
        print("List result:\n")
        print("Entries: {}".format(res), '\n')
        print('-------------------------------------------------------------------\n')
    except grpc.RpcError as exception:
        print(exception)
    return


def Delete(stub, obj):
    try: 
        res = stub.Delete(keyval_pb2.DeleteRequest(key=obj['key'],current_version=obj['current_version']))
        save_to_disk(res, 'Delete')
        print("Delete result:\n")
        print(res, '\n')
        print('-------------------------------------------------------------------\n')
    except grpc.RpcError as exception:
        print(exception)
    return


def basic_client_server_tests():
    try:
        channel1 = grpc.insecure_channel('localhost:50050')
        channel2 = grpc.insecure_channel('localhost:50051')

        stub1 = keyval_pb2_grpc.KeyValueStub(channel1)
        stub2 = keyval_pb2_grpc.KeyValueStub(channel2)

        for i in range(0, 10):
            key = 'ShardKey' + str(i)
            value = 'Value' + str(i)
            if i % 2 == 0:
                # Blind write: Write Key, Value with no version check
                Write(stub2, {'key': key, 'value': value, 'current_version': -1})
            else:
                # Blind write: Write Key, Value with no version check
                Write(stub1, {'key': key, 'value': value, 'current_version': -1})
        
        List(stub1)

        List(stub2)

    except grpc.RpcError as e:
        print("error: {0:s}: {1:s}".format(e.code(), e.details()))


if __name__ == '__main__':
    parseArgs()
    basic_client_server_tests()
