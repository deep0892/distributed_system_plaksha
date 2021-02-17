import collections
import os
import sys
import logging
import subprocess
import argparse
from google.protobuf import text_format
import keyval_pb2
import platform
import shutil

# The gRPC command line tool used to run the tests
if platform.system() == "Windows":
  grpc_cli = "grpc_cli.exe"
else:
  grpc_cli = "grpc_cli"

def GetLogFileDir():
  """Returns the directory set to store the environment file."""
  return "/tmp"

def BinaryArgsList(binary_path, params=None):
  """Constructs a list of the binary and its args.

  Arguments:
    binary_path: The path of the binary.
    params: A list of the parameters passed to the binary.

  Returns:
    A list of the google3 binary along with its arguments.

  Raises:
    BinaryNotFoundException: if the file does not exist at the given path.
  """
  if not shutil.which(binary_path, os.F_OK | os.X_OK):
    raise Exception("%s is not the path" % binary_path)
  result = [binary_path]
  # Then add the params
  if params:
    # parameters = params.split(" ")
    result.extend(params)
  return result

def Run(binary_path, params=None):
  """Run the given binary with the params.

  Arguments:
    binary_path: The path of the binary.
    params: A list of the parameters passed to the binary.

  Returns:
    The exit code returned by running the binary.
  """
  parser = argparse.ArgumentParser(description='Process driver args.')
  parser.add_argument("--use_log", action="store_true")
  args = parser.parse_args()
  log_locations = os.path.join(GetLogFileDir(), "driver.INFO")
  binary = BinaryArgsList(binary_path, params)
  if args.use_log:
      with open(log_locations, "w") as logfile:
          return subprocess.run(binary, stderr=logfile, stdout=logfile)
  else:
      if sys.version_info[1] >= 7:
        return subprocess.run(binary, capture_output=True)
      else:
        return subprocess.run(binary, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def CallParams(method_name, proto):
    """Returns the parameters for calling a gRPC method
    
    Arguments:
      method_name: Name of the remote method to be called
      proto: The protobuf to be passed to the RPC method

    Returns:
      The parameters thast can be passed to grpc_cli call
      to execute the RPC.
    """
    return ["--protofiles=keyval.proto", "--noremotedb", "call",
            "localhost:50050", "KeyValue." + method_name, proto]

def ExecuteWrite(key, value, current_version, success):
    """Executes a remote write and verifies that it executed as expected

    Arguments:
      key: The key of entry to be added/updated
      value: The new value for the given key
      current_version: The version that is expected to exist at the server.
                       If the version does not match what the server has,
                       the write fails. A value <=0 implies a blind write,
                       i.e., the existing version is ignored.
     success: If the write is expected to succeed.
    """
    write_proto = "key:'%s' value:'%s' current_version:%d" % (key, value,
                                                              current_version)
    process_result = Run(grpc_cli, CallParams("Write", write_proto))
    output_str = process_result.stdout.decode("utf-8")
    response = keyval_pb2.WriteResponse()
    print("Write Result:")
    print(text_format.Parse(output_str, response))
    assert response.status.ok == success, "Write call expected %s" % success
    assert response.status.server_id == 1, "Expected server id to be 1"
    new_version = current_version + 1
    if current_version < 0:
        new_version = 1
    if success:
        assert response.new_version == new_version, ("Expected version to be " +
                                                 "%s but got %s" % (new_version, response.new_version))
    print("-------------------------------------------------------------------")

def ExecuteRead(key, success, read_value, read_version):
    """Executes a remote read and verifies that it executed as expected

    Arguments:
      key: The key of entry to be read
      success: If the read is expected to succeed.
      read_value: The expected value to be read for the given key  (if success is True)
      read_version: The expected version to be read (if success is True)
    """
    process_result = Run(grpc_cli, CallParams("Read", "key: '%s'" % key))
    output_str = process_result.stdout.decode("utf-8")
    response = keyval_pb2.ReadResponse()
    print("Read Result:")
    print(text_format.Parse(output_str, response))
    assert response.status.ok == success, "Read call expected %s" % success
    assert response.status.server_id == 1, "Expected server id to be 1"
    if success:
        assert response.current_version == read_version, ("Expected version to be " +
                                                  "%s but got %s" % (read_version, response.current_version))
        assert response.value == read_value, ("Expected value to be " +
                                                  "%s but got %s" % (read_value, response.value))
    print("-------------------------------------------------------------------")

def ExecuteList(expected_entries):
    """Executes a remote list and verifies that it executed as expected

    Arguments:
      expected_entries: A list of 3-tuples (<key, value, version> of the
                        expected list of entries
    """
    process_result = Run(grpc_cli, CallParams("List", ""))
    output_str = process_result.stdout.decode("utf-8")
    response = keyval_pb2.ListResponse()
    print("List Result:")
    print(text_format.Parse(output_str, response))
    assert response.status.ok == True, "List call expected to be successful"
    assert response.status.server_id == 1, "Expected server id to be 1"
    # Go through the list
    expected_len = len(expected_entries)
    actual_len = len(response.entries)
    assert expected_len == actual_len, "Expected entries length to be %d but got %d" % (expected_len, actual_len)
    # XXX Check the results
    print("-------------------------------------------------------------------")

def ExecuteDelete(key, current_version, success, deleted_value, deleted_version):
    """Executes a remote delete and verifies that it executed as expected

    Arguments:
      key: The key of entry to be delete
      current_version: The version that is expected to exist at the server.
                       If the version does not match what the server has,
                       the delete fails. A value <=0 implies a blind delete,
                       i.e., the existing version is ignored.    
      success: If the delete is expected to succeed.
      deleted_value: The expected value to be deleted for the given key  (if success is True)
      deleted_version: The expected version to be deleted (if success is True)
    """
    delete_proto = "key: '%s' current_version: %d" % (key, current_version)
    process_result = Run(grpc_cli, CallParams("Delete", delete_proto))
    output_str = process_result.stdout.decode("utf-8")
    response = keyval_pb2.DeleteResponse()
    print("Delete Result:")
    print(text_format.Parse(output_str, response))
    assert response.status.ok == success, "Delete call expected %s" % success
    assert response.status.server_id == 1, "Expected server id to be 1. Was %s" % response.status.server_id
    if success:
        assert response.deleted_version == deleted_version, ("Expected version to be " +
                                                             "%s but got %s" % (deleted_version, response.deleted_version))
        assert response.deleted_value == deleted_value, ("Expected value to be " +
                                                 "%s but got %s" % (deleted_value, response.deleted_value))
    print("-------------------------------------------------------------------")
        
def BasicTest():
    """Some basic tests for all operations with valid protos
    """
    # Blind write
    ExecuteWrite("Key1", "Value1", -1, True)
    # Normal write
    ExecuteWrite("Key1", "Value2", 1, True)
    # Version check failure with version mismatch
    ExecuteWrite("Key1", "Value3", 1, False)
    # Version check failure with version missing
    ExecuteWrite("Key2", "Value3", 1, False)

    # Normal read
    ExecuteRead("Key1", True, "Value2", 2)
    # Non-existing read
    ExecuteRead("Key2", False, "", 0)

    # Check full state with List
    ExecuteList([("Key1", "Value1", 2)])
    # Add one more value and list 2 elements.
    ExecuteWrite("Key3", "Value3", -1, True)
    ExecuteList([("Key1", "Value1", 2), ("Key2", "Value3", 2)])

    # Delete with version check failure
    ExecuteDelete("Key1", 1, False, "", 1)
    # Normal delete
    ExecuteDelete("Key1", 2, True, "Value2", 2)
    # Delete non-existent
    ExecuteDelete("Key1", 2, False, "", 0)

    # Delete last element
    ExecuteDelete("Key3", 1, True, "Value3", 1)
    # Check state with List.
    ExecuteList([])

def ValidationTest():
    """Some basic tests for all operations with invalid protos
    """
    # Invalid write protos.
    ExecuteWrite("", "Value", 0, False)
    ExecuteWrite("Key", "", 0, False)
    ExecuteWrite("", "", 0, False)

    # Invalid read proto.
    ExecuteRead("", False, "", "")

    # Invalid delete proto.
    ExecuteDelete("", 10, False, "", "")
    ExecuteDelete("Key1", 0, False, "", "")

if __name__ == '__main__':
    logging.basicConfig()
    if sys.version_info[0] < 3:
      raise Exception("Must be using Python 3")
    BasicTest()
    ValidationTest()