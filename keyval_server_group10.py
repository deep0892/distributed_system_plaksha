from concurrent import futures
import argparse
import grpc
import logging
import socket
import sys
import time

# import ip
import keyval_pb2
import keyval_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

args = []
store = {}
peers = []

def parseArgs():
    global args
    parser = argparse.ArgumentParser(description="Key-value store server.")
    parser.add_argument("--server_id", default="1",
                        help="The id of the server (e.g., 1 or 2)")
    parser.add_argument("--write_delay", default="0",
                        help=" The delay in seconds that is added to the Write RPC handling in the server, i.e., before the Write RPC is handled on the server side.")
    parser.add_argument("--port", default="50050",
                        help="The port on which the server listens. Default: 50050")
    args = parser.parse_args()
    print('args', args)
    return args

class KeyValueServicer(keyval_pb2_grpc.KeyValueServicer):

    def Read(self, request, context):
        status = keyval_pb2.Status(server_id=int(args.server_id), ok=True)
        key = request.key
        if not key:
            error = f"Read aborted. Key not present"
            return keyval_pb2.ReadResponse(status=keyval_pb2.Status(server_id=int(args.server_id), ok=False, error=error))

        if key in store and key in store[key]:
            temp = store[key]
            return keyval_pb2.ReadResponse(status=status, key=key, value=temp[key], current_version=temp['current_version'])
        else:
            error = f"Read aborted. Key not present {key}"
            return keyval_pb2.ReadResponse(status=keyval_pb2.Status(server_id=int(args.server_id), ok=False, error=error))

    def Write(self, request, context):
        key = request.key
        value = request.value
        current_version = request.current_version
        error = ''
        try:
            time.sleep(float(args.write_delay))
            if not key:
                error = f"Write aborted. Key not present"
                return keyval_pb2.WriteResponse(status=keyval_pb2.Status(server_id=int(args.server_id), ok=False, error=error), key=key)

            if not value:
                error = f"Write aborted. Value not present"
                return keyval_pb2.WriteResponse(status=keyval_pb2.Status(server_id=int(args.server_id), ok=False, error=error), key=key)

            status = keyval_pb2.Status(server_id=int(args.server_id), ok=True)
            temp = store.get(key, {})
            
            if 'current_version' in temp and  current_version > 0 and current_version != temp['current_version']:
                error = f"Write aborted. Record version mismatch. Expected = {current_version}, Actual = {temp['current_version']}"
                return keyval_pb2.WriteResponse(status=keyval_pb2.Status(server_id=int(args.server_id), ok=False, error=error), key=key, new_version=temp['current_version'])
            elif 'current_version' not in temp and  current_version > 0 :
                error = f"Write aborted. Record missing but Write expected value to exist at version 1"
                return keyval_pb2.WriteResponse(status=keyval_pb2.Status(server_id=int(args.server_id), ok=False, error=error), key=key, new_version=current_version)

            if not temp or current_version < 0:
                temp['current_version'] = 1
            else:
                temp['current_version'] += 1
            
            temp[key] = value
            store[key] = temp

            return keyval_pb2.WriteResponse(status=status, key=key, new_version=temp['current_version'])
        except grpc.RpcError as exception:
            error = f"Write aborted. Exception: {exception}"
            return keyval_pb2.WriteResponse(status=keyval_pb2.Status(server_id=int(args.server_id), ok=False, error=error), key=key, new_version=current_version)

    def Delete(self, request, context):
        status = keyval_pb2.Status(server_id=int(args.server_id), ok=True)
        key = request.key
        current_version = request.current_version
        
        if key not in store:
            error = f"Key not present {key}"
            return keyval_pb2.DeleteResponse(status=keyval_pb2.Status(server_id=int(args.server_id), ok=False, error=error))
        
        temp = store[key]
        value = temp[key]
        
        if temp['current_version'] != current_version and current_version >= 0 :
            error = f"Delete aborted. Record version mismatch: Expected = {current_version}, Actual = {temp['current_version']}"
            return keyval_pb2.DeleteResponse(status=keyval_pb2.Status(server_id=int(args.server_id), ok=False, error=error))
        
        del store[key]
        
        return keyval_pb2.DeleteResponse(status=status, key=key, deleted_value=value, deleted_version=temp['current_version'])

    def List(self, request, context):
        status = keyval_pb2.Status(server_id=int(args.server_id), ok=True)
        entries = []

        for key in store.keys():
            temp = store[key]
            entries.append({"key": key, 
                            "value":temp[key],
                            "current_version":temp['current_version']})
        
        return keyval_pb2.ListResponse(status=status, entries=entries)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    keyval_pb2_grpc.add_KeyValueServicer_to_server(KeyValueServicer(), server)
    server.add_insecure_port('[::]:' + args.port)
    server.start()
    print('Start of server ...................... at PORT: ' + args.port)
    try:
        while True:
            time.sleep(float(_ONE_DAY_IN_SECONDS))
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    args = parseArgs()
    serve()