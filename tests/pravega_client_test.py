#
# Copyright (c) Dell Inc., or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#

import unittest
import secrets
import string
import pravega_client
from pravega_client import TxnFailedException
from pravega_client import StreamScalingPolicy
from pravega_client import StreamRetentionPolicy

class PravegaTest(unittest.TestCase):

    def test_tags(self):
        scope = ''.join(secrets.choice(string.ascii_lowercase + string.digits)
                        for i in range(10))
        print("Creating a Stream Manager, ensure Pravega is running")
        stream_manager=pravega_client.StreamManager("tcp://127.0.0.1:9090", False, False)

        print("Creating a scope")
        scope_result=stream_manager.create_scope(scope)
        self.assertEqual(True, scope_result, "Scope creation status")
        print("Creating a stream")
        # stream is created using a fixed scaling policy.
        stream_result=stream_manager.create_stream(scope, "testStream", 1)
        self.assertTrue(stream_result, "Stream creation status")
        tags = stream_manager.get_stream_tags(scope, "testStream")
        # verify empty tags.
        self.assertTrue(len(tags)==0)
        stream_update=stream_manager.update_stream_with_policy(scope_name=scope, stream_name="testStream", tags=["t1"])
        self.assertTrue(stream_update, "Stream update status")
        tags = stream_manager.get_stream_tags(scope, "testStream")
        self.assertEqual(["t1"], tags)

        # create a stream with stream scaling is enabled with data rate as 10kbps, scaling factor as 2 and initial segments as 1
        policy = StreamScalingPolicy.auto_scaling_policy_by_data_rate(10, 2, 1)
        retention = StreamRetentionPolicy.none()
        stream_result=stream_manager.create_stream_with_policy(scope_name=scope, stream_name="testStream1", scaling_policy=policy, retention_policy=retention)
        self.assertTrue(stream_result, "Stream creation status")
        # add tags
        stream_update=stream_manager.update_stream_with_policy(scope_name=scope, stream_name="testStream1", scaling_policy=policy, tags=['t1', 't2'])
        self.assertTrue(stream_update, "Stream update status")
        tags = stream_manager.get_stream_tags(scope, "testStream1")
        self.assertEqual(['t1', 't2'], tags)

        # update retention policy
        # retention policy of 10GB
        retention = StreamRetentionPolicy.by_size(10*1024*1024 * 1024)
        stream_update=stream_manager.update_stream_with_policy(scope, "testStream1", policy, retention, tags=["t4", "t5"])
        self.assertTrue(stream_update, "Stream update status")
        tags = stream_manager.get_stream_tags(scope, "testStream1")
        self.assertEqual(["t4", "t5"], tags)

        # test for list_scope API
        scope_list = stream_manager.list_scope()
        self.assertTrue(len(scope_list) > 0, "The scope list is empty")
        # test for list_stream API
        scope_name = str(scope_list[0])
        self.assertTrue(scope_name, "The scope name is empty")
        stream_list = stream_manager.list_stream(scope_name)
        self.assertTrue(len(stream_list) > 0, "The stream list is empty")
        # test with false scope name for list_stream API
        false_scope = "falsescope"
        stream_list1 = stream_manager.list_stream(false_scope)
        self.assertEqual(stream_list1, [])
        # test with empty scope name for list_stream API
        empty_string = ""
        stream_list2 = stream_manager.list_stream(empty_string)
        self.assertEqual(stream_list2, [])

    def test_writeEvent(self):
        scope = ''.join(secrets.choice(string.ascii_lowercase + string.digits)
                        for i in range(10))
        print("Creating a Stream Manager, ensure Pravega is running")
        stream_manager=pravega_client.StreamManager("tcp://127.0.0.1:9090", False, False)

        print("Creating a scope")
        scope_result=stream_manager.create_scope(scope)
        self.assertEqual(True, scope_result, "Scope creation status")

        print("Creating a stream")
        stream_result=stream_manager.create_stream(scope, "testStream", 1)
        self.assertEqual(True, stream_result, "Stream creation status")

        print("Creating a writer for Stream")
        w1=stream_manager.create_writer(scope,"testStream")

        print("Write events")
        w1.write_event("test event1")
        w1.write_event("test event2")

    def test_deleteScope(self):
        scope = ''.join(secrets.choice(string.ascii_lowercase + string.digits)
                        for i in range(10))
        print("Creating a Stream Manager, ensure Pravega is running")
        stream_manager=pravega_client.StreamManager("tcp://127.0.0.1:9090", False, False)

        print("Creating a scope")
        scope_result=stream_manager.create_scope(scope)
        self.assertEqual(True, scope_result, "Scope creation status")

        print("Deleting the scope")
        delete_scope_result=stream_manager.delete_scope(scope)
        self.assertEqual(True, delete_scope_result, "Scope deletion status")

    def test_seal_deleteStream(self):
        scope = ''.join(secrets.choice(string.ascii_lowercase + string.digits)
                        for i in range(10))
        print("Creating a Stream Manager, ensure Pravega is running")
        stream_manager=pravega_client.StreamManager("tcp://127.0.0.1:9090", False, False)
        print(repr(stream_manager))
        print("Creating a scope")
        scope_result=stream_manager.create_scope(scope)
        self.assertEqual(True, scope_result, "Scope creation status")

        print("Creating a stream")
        stream_result=stream_manager.create_stream(scope, "testSealStream", 1)
        self.assertEqual(True, stream_result, "Stream creation status")

        policy = StreamScalingPolicy.auto_scaling_policy_by_event_rate(10, 2, 1)
        retention = StreamRetentionPolicy.by_time(24*60*60*1000)
        stream_update=stream_manager.update_stream_with_policy(scope, "testSealStream", policy, retention)
        self.assertTrue(stream_update, "Stream update status")

        print("Creating a writer for Stream")
        w1=stream_manager.create_writer(scope,"testSealStream")

        print("Write events")
        w1.write_event("test event1", "key")
        w1.write_event("test event2", "key")

        seal_stream_status = stream_manager.seal_stream(scope, "testSealStream")
        self.assertTrue(seal_stream_status, "Stream seal status")

        try:
            w1.write_event("test event3", "key")
            self.fail("Writing to an already sealed stream should throw exception")
        except Exception as e:
            print("Exception ", e)

        delete_stream_status = stream_manager.delete_stream(scope, "testSealStream")
        self.assertTrue(delete_stream_status, "Stream deletion status")

    def test_byteStream(self):
        scope = ''.join(secrets.choice(string.ascii_lowercase + string.digits)
                        for i in range(10))
        print("Creating a Stream Manager, ensure Pravega is running")
        stream_manager=pravega_client.StreamManager("tcp://127.0.0.1:9090", False, False)

        print("Creating a scope")
        scope_result=stream_manager.create_scope(scope)
        self.assertEqual(True, scope_result, "Scope creation status")

        print("Creating a stream")
        stream_result=stream_manager.create_stream(scope, "testStream", 1)
        self.assertEqual(True, stream_result, "Stream creation status")

        # write and read data.
        print("Creating a writer for Stream")
        bs=stream_manager.create_byte_stream(scope,"testStream")
        print(repr(bs))
        self.assertEqual(15, bs.write(b"bytesfortesting"))
        self.assertEqual(15, bs.write(b"bytesfortesting"))
        self.assertEqual(15, bs.write(b"bytesfortesting"))
        bs.flush()
        self.assertEqual(45, bs.current_tail_offset())
        buf=bytearray(10)
        self.assertEqual(10, bs.readinto(buf))

        # fetch the current read offset.
        current_offset=bs.tell()
        self.assertEqual(10, current_offset)
        self.assertTrue(bs.seekable())

        # seek to a given offset and read
        bs.seek(10, 0)
        buf=bytearray(2)
        self.assertEqual(2, bs.readinto(buf))
        current_offset=bs.tell()
        self.assertEqual(12, current_offset)

        # seek from {current position (i.e. 12 here) + 5 } which is 17 and read
        bs.seek(5, 1)
        buf=bytearray(8)
        # reading 8 bytes here
        self.assertEqual(8, bs.readinto(buf))
        self.assertEqual(25, bs.tell())

        # seek from {size of this object (i.e. 45 here) - 10 } which is 35 and read
        bs.seek(-10, 2)
        buf=bytearray(8)
        # reading 8 bytes here
        self.assertEqual(8, bs.readinto(buf))
        self.assertEqual(43, bs.tell())

        bs.truncate(2)
        self.assertEqual(2, bs.current_head_offset())
        try:
            bs.seek(3, 6)
            self.fail("whence should be one of 0: seek from start, 1: seek from current, or 2: seek from end")
        except Exception as e:
            print("Exception ", e)

    def test_writeTxn(self):
        scope = ''.join(secrets.choice(string.ascii_lowercase + string.digits)
                        for i in range(10))
        print("Creating a Stream Manager, ensure Pravega is running")
        stream_manager=pravega_client.StreamManager("tcp://127.0.0.1:9090")

        print("Creating a scope")
        scope_result=stream_manager.create_scope(scope)
        self.assertEqual(True, scope_result, "Scope creation status")

        print("Creating a stream")
        stream_result=stream_manager.create_stream(scope, "testTxn", 1)
        self.assertEqual(True, stream_result, "Stream creation status")

        print("Creating a txn writer for Stream")
        w1=stream_manager.create_transaction_writer(scope,"testTxn", 1)
        print(repr(w1))
        txn1 = w1.begin_txn()
        print(repr(txn1))
        txn1_id = txn1.get_txn_id()
        print("Write events")
        txn1.write_event("test event1")
        txn1.write_event("test event2")
        self.assertTrue(txn1.is_open(), "Transaction is open")
        print("commit transaction")
        txn1.commit()
        get_txn = w1.get_txn(txn1_id)
        self.assertEqual(False, get_txn.is_open(), "Transaction is closed")

        txn2 = w1.begin_txn()
        print("Write events")
        txn2.write_event("test event1")
        txn2.write_event("test event2")
        self.assertTrue(txn2.is_open(), "Transaction is open")
        print("commit transaction")
        txn2.abort()
        self.assertEqual(False, txn2.is_open(), "Transaction is closed")

    def test_TxnError(self):
        scope = ''.join(secrets.choice(string.ascii_lowercase + string.digits)
                        for i in range(10))

        print("Creating a Stream Manager, ensure Pravega is running")
        stream_manager=pravega_client.StreamManager("tcp://127.0.0.1:9090")

        print("Creating a scope")
        scope_result=stream_manager.create_scope(scope)
        self.assertEqual(True, scope_result, "Scope creation status")

        print("Creating a stream")
        stream_result=stream_manager.create_stream(scope, "testTxn", 1)
        self.assertEqual(True, stream_result, "Stream creation status")

        print("Creating a txn writer for Stream")
        w1=stream_manager.create_transaction_writer(scope,"testTxn", 1)
        txn1 = w1.begin_txn()
        print("Write events")
        txn1.write_event("test event1")
        txn1.write_event("test event2")
        self.assertTrue(txn1.is_open(), "Transaction is open")
        print("commit transaction")
        txn1.commit()
        self.assertEqual(False, txn1.is_open(), "Transaction is closed")

        #Attempt writing to an already commited transaction.
        try:
            txn1.write_event("Error")
            self.fail("Write on an already closed transaction should throw a TxnFailedException")
        except TxnFailedException as e:
            print("Exception ", e)

        #Attempt committing an closed transaction.
        try:
            txn1.commit()
            self.fail("Commit of an already closed transaction should throw a TxnFailedException")
        except TxnFailedException as e:
            print("Exception ", e)

        #Attempt aborting an closed transaction.
        try:
            txn1.abort()
            self.fail("Abort of an already closed transaction should throw a TxnFailedException")
        except TxnFailedException as e:
            print("Exception ", e)

if __name__ == '__main__':
    unittest.main()