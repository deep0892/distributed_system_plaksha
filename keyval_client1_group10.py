from __future__ import print_function
import argparse
import keyval_pb2
import keyval_pb2_grpc
import grpc
import logging
import re
import sys
import time


def save_to_disk(res, op):
    with open("tmp/foo.txt", "a") as myfile:
        myfile.write(op + ' result:\n')
        myfile.write(str(res) + '\n')
        myfile.write('-------------------------------------------------------------------\n')
    return    

def Read(stub, obj):

    req = keyval_pb2.ReadRequest(key=obj['key'])
    res = stub.Read(req)

    save_to_disk(res, 'Read')
    print("Read result:\n")
    print(res,'\n')
    print('-------------------------------------------------------------------\n')
        

def Write(stub, obj):
    res  = stub.Write(keyval_pb2.WriteRequest(key=obj['key'],value=obj['value'],current_version=obj['current_version']))
    save_to_disk(res, 'Write')
    print("Write result:\n")
    print(res, '\n')
    print('-------------------------------------------------------------------\n')
    return
    

def List(stub):
    res = stub.List(keyval_pb2.ListRequest())
    save_to_disk(res, 'List')
    print("List result:\n")
    print("Entries: {}".format(res), '\n')
    print('-------------------------------------------------------------------\n')
    return


def Delete(stub, obj):
    res = stub.Delete(keyval_pb2.DeleteRequest(key=obj['key'],current_version=obj['current_version']))
    save_to_disk(res, 'Delete')
    print("Delete result:\n")
    print(res, '\n')
    print('-------------------------------------------------------------------\n')
    return


def run():
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

if __name__ == '__main__':
    run()
