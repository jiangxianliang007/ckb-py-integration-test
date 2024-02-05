import time

from framework.basic import CkbTest

from datetime import datetime


class TestCkbDisconnectFetchTransactionSoloNodes(CkbTest):

    @classmethod
    def setup_class(cls):
        nodes = [
            cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "cluster2/node{i}".format(i=i), 8214 + i,
                                         8225 + i)
            for
            i in range(1, 2)]
        cls.cluster = cls.Cluster(nodes)
        cls.cluster.prepare_all_nodes()
        cls.cluster.start_all_nodes()
        cls.cluster.connected_all_nodes()
        cls.Miner.make_tip_height_number(cls.cluster.ckb_nodes[0], 100)
        cls.Node.wait_cluster_height(cls.cluster, 100, 1000)
        # link ckb-light-client
        cls.ckb_light_node = cls.CkbLightClientNode.init_by_nodes(cls.CkbLightClientConfigPath.CURRENT_TEST,
                                                                  cls.cluster.ckb_nodes,
                                                                  "tx_pool_light2/node1", 8201)

        cls.account = cls.Ckb_cli.util_key_info_by_private_key(cls.Config.MINER_PRIVATE_1)

        cls.ckb_light_node.prepare()
        cls.ckb_light_node.start()
        cls.ckb_light_node.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": '0x1234'}, "script_type": "lock", "block_number": "0x0"}])
        cls.Node.wait_light_sync_height(cls.ckb_light_node, 5, 3000)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()
        cls.ckb_light_node.stop()
        cls.ckb_light_node.clean()

    def test_fetch_transaction_when_solo_ckb_restart(self):
        """
        1. fetchTransaction
            successful
        2. wait fetchTransaction.status == fetching, restart ckb  and miner
            ok
        3. fetchTransaction
            successful
            status == fetched
        """
        # fetchTransaction
        client = self.cluster.ckb_nodes[0].getClient()
        block = client.get_block_by_number(hex(100))
        tx_hash = block['transactions'][0]['hash']
        while True:
            state = self.ckb_light_node.getClient().fetch_transaction(tx_hash)
            print(state['status'])
            if state['status'] != "added":
                break
        self.cluster.restart_all_node()
        self.cluster.connected_all_nodes()
        self.cluster.ckb_nodes[0].start_miner()
        current_time = datetime.now()
        for i in range(200):
            self.ckb_light_node.getClient().get_scripts()
            state = self.ckb_light_node.getClient().fetch_transaction(tx_hash)
            print(state['status'])
            time.sleep(2)
            if state['status'] != "fetching":
                end_time = datetime.now()
                time_difference = end_time - current_time
                print("cost time:", time_difference)
                return
        assert False
