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
        with grpc.insecure_channel('localhost:50050') as channel:
            stub = keyval_pb2_grpc.KeyValueStub(channel)

            # operations to be performed as stated in client implementation.
            # Blind write: Write Key1, Value1 with no version check
            Write(stub, {'key':'Key1','value':'Value1','current_version':-1})
            
            # Normal write: Write Key1, Value1 expecting the current version to be 1
            Write(stub, {'key':'Key1','value':'Value2','current_version':1})
            
            # Version check failure: Write Key1, Value3 expecting the current version to be 1
            Write(stub, {'key':'Key1','value':'Value3','current_version':1})
            
            # Version failure with key missing: Write Key2, Value3, 1
            Write(stub, {'key':'Key2','value':'Value3','current_version':2})
            
            # Normal read: Read Key1
            Read(stub, {'key':'Key1'})
                                                                                                                    
            # Non-existing key read: Read Key2
            Read(stub, {'key':'Key2'})

            # Get full state with List: List
            List(stub)
                                                                                                                        
            # Add new element as a blind write: Write Key3, Value3
            Write(stub, {'key':'Key3','value':'Value3','current_version':-1})
            
            # Get full state with List: List
            List(stub)
            
            # Delete with version check failure: Delete Key1 with current_version stated as 1
            Delete(stub, {'key':'Key1','current_version':1})
            
            # Normal delete: Delete Key1 with current_version stated as 2
            Delete(stub, {'key':'Key1','current_version':2})
            
            # Delete of a non-existent key: Delete Key1 with current_version as 2
            Delete(stub, {'key':'Key1','current_version':2})
            
            # Delete last element: Delete Key3 with current_version as 1
            Delete(stub, {'key':'Key3','current_version':1})
            
            # Get full state with List: List
            List(stub)

    except grpc.RpcError as e:
        print("error: {0:s}: {1:s}".format(e.code(), e.details()))

def expriment1_A():
    try:
        with grpc.insecure_channel('localhost:50050') as channel:
            stub = keyval_pb2_grpc.KeyValueStub(channel)

            # 
            # Blind write: Write Key0, Value0 with no version check
            Write(stub, {'key': 'Key0', 'value': 'Value0', 'current_version': -1}, float(args.write_timeout))
            
            # Blind write: Write Key1, Value1 with no version check
            Write(stub, {'key': 'Key1', 'value': 'Value1', 'current_version': -1}, float(args.write_timeout))

            # Blind write: Write Key2, Value2 with no version check
            Write(stub, {'key': 'Key2', 'value': 'Value2', 'current_version': -1}, float(args.write_timeout))
            
            # Blind write: Write Key3, Value3 with no version check
            Write(stub, {'key': 'Key3', 'value': 'Value3', 'current_version': -1}, float(args.write_timeout))
            
            # Blind write: Write Key4, Value4 with no version check
            Write(stub, {'key':'Key4','value':'Value4','current_version':-1}, float(args.write_timeout))
            
            # Sleep for 5 sec
            time.sleep(5)

            # Get full state with List: List
            List(stub)
            
            
            #  Delete Key0 with current_version stated as 1
            Delete(stub, {'key':'Key0','current_version':1})
            
            # Delete Key1 with current_version stated as 1
            Delete(stub, {'key':'Key1','current_version':1})
            
            # Delete Key2 with current_version stated as 1
            Delete(stub, {'key':'Key2','current_version':1})
            
            # Delete Key3 with current_version stated as 1
            Delete(stub, {'key':'Key3', 'current_version': 1})
            
            # Delete Key4 with current_version stated as 1
            Delete(stub, {'key':'Key4','current_version':1})
            
            # Get full state with List: List
            List(stub)

    except grpc.RpcError as e:
        print("error: {0:s}: {1:s}".format(e.code(), e.details()))

def expriment1_B():
    try:
        with grpc.insecure_channel('localhost:50050') as channel:
            stub = keyval_pb2_grpc.KeyValueStub(channel)

            # 
            # Blind write: Write Key0, Value0 with no version check
            Write(stub, {'key': 'Key0', 'value': 'Value0', 'current_version': -1}, float(args.write_timeout))
            
            # Blind write: Write Key1, Value1 with no version check
            Write(stub, {'key': 'Key1', 'value': 'Value1', 'current_version': -1}, float(args.write_timeout))

            # Blind write: Write Key2, Value2 with no version check
            Write(stub, {'key': 'Key2', 'value': 'Value2', 'current_version': -1}, float(args.write_timeout))
            
            # Blind write: Write Key3, Value3 with no version check
            Write(stub, {'key': 'Key3', 'value': 'Value3', 'current_version': -1}, float(args.write_timeout))
            
            # Blind write: Write Key4, Value4 with no version check
            Write(stub, {'key':'Key4','value':'Value4','current_version':-1}, float(args.write_timeout))
            

            # Get full state with List: List
            List(stub)
            
            
            #  Delete Key0 
            Delete(stub, {'key':'Key0','current_version':-1})
            
            # Delete Key1 
            Delete(stub, {'key':'Key1','current_version':-1})
            
            # Delete Key2 
            Delete(stub, {'key':'Key2','current_version':-1})
            
            # Delete Key3 
            Delete(stub, {'key':'Key3', 'current_version':-1})
            
            # Delete Key4 
            Delete(stub, {'key':'Key4','current_version':-1})
            
            # Get full state with List: List
            List(stub)

    except grpc.RpcError as e:
        print("error: {0:s}: {1:s}".format(e.code(), e.details()))


def expriment2():
    try:
        with grpc.insecure_channel('localhost:50050') as channel:
            stub = keyval_pb2_grpc.KeyValueStub(channel)

            # 
            # Blind write: Write Key1, Value1 with no version check
            Write(stub, {'key': 'Key1', 'value': 'Value1', 'current_version': -1}, float(args.write_timeout))

            #  Delete Key1 with current_version stated as -1
            Delete(stub, {'key':'Key1','current_version':-1})
            
            # Sleep for 1 sec
            time.sleep(1)

            # Get full state with List: List
            List(stub)

    except grpc.RpcError as e:
        print("error: {0:s}: {1:s}".format(e.code(), e.details()))


if __name__ == '__main__':
    parseArgs()
    basic_client_server_tests()
    # expriment1_A()
    # expriment1_B()
    # expriment2()
