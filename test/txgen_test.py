import unittest
import shutil

from tinman import prockey
from tinman import txgen

FULL_CONF = {
    "transactions_per_block" : 40,
    "steem_block_interval" : 3,
    "num_blocks_to_clear_witness_round" : 21,
    "transaction_witness_setup_pad" : 100,
    "steem_max_authority_membership" : 10,
    "steem_address_prefix" : "TST",
    "steem_init_miner_name" : 'initminer',
    "snapshot_file" : "/tmp/test-snapshot.json",
    "backfill_file" : "/tmp/test-backfill.actions",
    "min_vesting_per_account" : {"amount" : "1", "precision" : 3, "nai" : "@@000000021"},
    "total_port_balance" : {"amount" : "200000000000", "precision" : 3, "nai" : "@@000000021"},
    "accounts" : {
        "initminer" : {
            "name" : "initminer",
            "vesting" : {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"}
        }, "init" : {
            "name" : "init-{index}",
            "vesting" : {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"},
            "count" : 21,
            "creator" : "initminer"
        }, "elector" : {
            "name" : "elect-{index}",
            "vesting" : {"amount" : "1000000000", "precision" : 3, "nai" : "@@000000021"},
            "count" : 10,
            "round_robin_votes_per_elector" : 2,
            "random_votes_per_elector" : 3,
            "randseed" : 1234,
            "creator" : "initminer"
        }, "porter" : {
            "name" : "porter",
            "creator" : "initminer",
            "vesting" : {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"}
        }, "manager" : {
            "name" : "tnman",
            "creator" : "initminer",
            "vesting" : {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"}
        },
            "STEEM_MINER_ACCOUNT" : {"name" : "mners"},
            "STEEM_NULL_ACCOUNT" : {"name" : "null"},
            "STEEM_TEMP_ACCOUNT" : {"name" : "temp"}
        }
    }

class TxgenTest(unittest.TestCase):

    def test_create_system_accounts_bad_args(self):
        self.assertRaises(TypeError, txgen.create_system_accounts)
    
    def test_create_witnesses(self):
        keydb = prockey.ProceduralKeyDatabase()
        conf = {"accounts": {
            "init": {
                "name" : "init-{index}",
                "vesting" : {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"},
                "count" : 21,
                "creator" : "initminer"
            }
        }}
        
        for witness in txgen.create_system_accounts(conf, keydb, "init"):
            self.assertEqual(len(witness["operations"]), 2)
            self.assertEqual(len(witness["wif_sigs"]), 1)
            account_create_operation, transfer_to_vesting_operation = witness["operations"]
            
            self.assertEqual(account_create_operation["type"], "account_create_operation")
            value = account_create_operation["value"]
            self.assertEqual(value["fee"], {"amount" : "0", "precision" : 3, "nai" : "@@000000021"})
            self.assertEqual(value["creator"], "initminer")
            
            self.assertEqual(transfer_to_vesting_operation["type"], "transfer_to_vesting_operation")
            value = transfer_to_vesting_operation["value"]
            self.assertEqual(value["from"], "initminer")
            self.assertEqual(value["amount"], {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"})

    def test_update_witnesses(self):
        keydb = prockey.ProceduralKeyDatabase()
        conf = {"accounts": {
            "init": {
                "name" : "init-{index}",
                "vesting" : {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"},
                "count" : 21,
                "creator" : "initminer"
            }
        }}
        
        for witness in txgen.update_witnesses(conf, keydb, "init"):
            self.assertEqual(len(witness["operations"]), 1)
            self.assertEqual(len(witness["wif_sigs"]), 1)
            
            for op in witness["operations"]:
                self.assertEqual(op["type"], "witness_update_operation")
                value = op["value"]
                self.assertEqual(value["url"], "https://steemit.com/")
                self.assertEqual(value["props"], {})
                self.assertEqual(value["fee"], {"amount" : "0", "precision" : 3, "nai" : "@@000000021"})

    def test_vote_witnesses(self):
        keydb = prockey.ProceduralKeyDatabase()
        conf = {"accounts": {
            "init": {
                "name" : "init-{index}",
                "vesting" : {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"},
                "count" : 21,
                "creator" : "initminer"
            }, "elector" : {
                "name" : "elect-{index}",
                "vesting" : {"amount" : "1000000000", "precision" : 3, "nai" : "@@000000021"},
                "count" : 10,
                "round_robin_votes_per_elector" : 2,
                "random_votes_per_elector" : 3,
                "randseed" : 1234,
                "creator" : "initminer"
            }
        }}
        
        for witness in txgen.vote_accounts(conf, keydb, "elector", "init"):
            self.assertGreater(len(witness["operations"]), 1)
            self.assertEqual(len(witness["wif_sigs"]), 1)
            
            for op in witness["operations"]:
                self.assertEqual(op["type"], "account_witness_vote_operation")
                value = op["value"]
                self.assertTrue(value["approve"])

    def test_get_account_stats(self):
        shutil.copyfile("test-snapshot.json", "/tmp/test-snapshot.json")
        conf = {
          "snapshot_file" : "/tmp/test-snapshot.json",
          "accounts": {}
        }
        
        account_stats = txgen.get_account_stats(conf)
        expected_account_names = {"steemit", "binance-hot", "alpha",
            "upbitsteemhot", "blocktrades", "steemit2", "ned", "holiday",
            "imadev", "muchfun", "poloniex", "gopax-deposit", "dan",
            "bithumb.sunshine", "ben", "dantheman", "openledger-dex", "bittrex",
            "huobi-withdrawal", "korbit3", "hellosteem"
        }
        
        self.assertEqual(account_stats["account_names"], expected_account_names)
        self.assertEqual(account_stats["total_vests"], 103927120221962824)
        self.assertEqual(account_stats["total_steem"], 60859732440)

    def test_get_proportions(self):
        shutil.copyfile("test-snapshot.json", "/tmp/test-snapshot.json")
        conf = {
          "snapshot_file" : "/tmp/test-snapshot.json",
          "min_vesting_per_account": {"amount" : "1", "precision" : 3, "nai" : "@@000000021"},
          "total_port_balance" : {"amount" : "200000000000", "precision" : 3, "nai" : "@@000000021"},
          "accounts": {}
        }
        account_stats = txgen.get_account_stats(conf)
        proportions = txgen.get_proportions(account_stats, conf)
        
        self.assertEqual(proportions["min_vesting_per_account"], 1)
        self.assertEqual(proportions["vest_conversion_factor"], 1469860)
        self.assertEqual(proportions["steem_conversion_factor"], 776237928593)

    def test_create_accounts(self):
        shutil.copyfile("test-snapshot.json", "/tmp/test-snapshot.json")
        conf = {
          "snapshot_file" : "/tmp/test-snapshot.json",
          "min_vesting_per_account": {"amount" : "1", "precision" : 3, "nai" : "@@000000021"},
          "total_port_balance" : {"amount" : "200000000000", "precision" : 3, "nai" : "@@000000021"},
          "accounts": {"porter": {"name": "porter"}
          }
        }
        keydb = prockey.ProceduralKeyDatabase()
        account_stats = txgen.get_account_stats(conf)
        
        for account in txgen.create_accounts(account_stats, conf, keydb):
            self.assertEqual(len(account["operations"]), 3)
            self.assertEqual(len(account["wif_sigs"]), 1)
            
            for op in account["operations"]:
                value = op["value"]
                if op["type"] == "account_create_operation":
                    self.assertEqual(value["fee"], {"amount" : "0", "precision" : 3, "nai" : "@@000000021"})
                elif op["type"] == "transfer_to_vesting_operation":
                    self.assertEqual(value["from"], "porter")
                    self.assertGreater(int(value["amount"]["amount"]), 0)
                elif op["type"] == "transfer_operation":
                    self.assertEqual(value["from"], "porter")
                    self.assertGreater(int(value["amount"]["amount"]), 0)
                    self.assertEqual(value["memo"], "Ported balance")


    def test_update_accounts(self):
        shutil.copyfile("test-snapshot.json", "/tmp/test-snapshot.json")
        conf = {
          "snapshot_file" : "/tmp/test-snapshot.json",
          "min_vesting_per_account": {"amount" : "1", "precision" : 3, "nai" : "@@000000021"},
          "total_port_balance" : {"amount" : "200000000000", "precision" : 3, "nai" : "@@000000021"},
          "accounts": {"manager": {"name": "tnman"}
          }
        }
        keydb = prockey.ProceduralKeyDatabase()
        account_stats = txgen.get_account_stats(conf)
        
        for account in txgen.update_accounts(account_stats, conf, keydb):
            self.assertEqual(len(account["operations"]), 1)
            self.assertEqual(len(account["wif_sigs"]), 1)
            for op in account["operations"]:
                value = op["value"]
                self.assertIn(["tnman", 1], value["owner"]["account_auths"])
                self.assertLessEqual(len(value["owner"]["account_auths"]), txgen.STEEM_MAX_AUTHORITY_MEMBERSHIP)
                self.assertLessEqual(len(value["active"]["account_auths"]), txgen.STEEM_MAX_AUTHORITY_MEMBERSHIP)
                self.assertLessEqual(len(value["posting"]["account_auths"]), txgen.STEEM_MAX_AUTHORITY_MEMBERSHIP)
                self.assertLessEqual(len(value["owner"]["key_auths"]), txgen.STEEM_MAX_AUTHORITY_MEMBERSHIP)
                self.assertLessEqual(len(value["active"]["key_auths"]), txgen.STEEM_MAX_AUTHORITY_MEMBERSHIP)
                self.assertLessEqual(len(value["posting"]["key_auths"]), txgen.STEEM_MAX_AUTHORITY_MEMBERSHIP)
            
    def test_build_actions(self):
        shutil.copyfile("test-snapshot.json", "/tmp/test-snapshot.json")
        shutil.copyfile("test-backfill.actions", "/tmp/test-backfill.actions")
        
        for action in txgen.build_actions(FULL_CONF):
            cmd, args = action
            
            if cmd == "metadata":
                if not args.get("post_backfill"):
                    self.assertEqual(args["txgen:semver"], "0.2")
                    self.assertEqual(args["txgen:transactions_per_block"], 40)
                    self.assertIsNotNone(args["epoch:created"])
                    self.assertEqual(args["actions:count"], 73)
                    self.assertGreater(args["recommend:miss_blocks"], 28631339)
                    self.assertEqual(args["snapshot:semver"], "0.2")
                    self.assertEqual(args["snapshot:origin_api"], "http://calculon.local")
            elif cmd == "wait_blocks":
                self.assertGreater(args["count"], 0)
            elif cmd == "submit_transaction":
                self.assertGreater(len(args["tx"]["operations"]), 0)
                self.assertIsInstance(args["tx"]["wif_sigs"], list)
                for wif in args["tx"]["wif_sigs"]:
                    if isinstance(wif, str):
                        esc = args.get("esc", None)
                        
                        if esc and len(wif) < 51:
                            self.assertEqual(esc, wif[0])
                            self.assertEqual(esc, wif[-1])
                        else:
                            self.assertEqual(len(wif), 51)
                    else:
                        self.assertIsInstance(wif, prockey.ProceduralPrivateKey)
            else:
                self.fail("Unexpected action: %s" % cmd)

    def test_build_actions_future_snapshot(self):
        shutil.copyfile("test-future-snapshot.json", "/tmp/test-future-snapshot.json")
        conf = FULL_CONF.copy()
        conf["snapshot_file"] = "/tmp/test-future-snapshot.json"
        
        with self.assertRaises(RuntimeError) as ctx:
            for action in txgen.build_actions(conf):
                cmd, args = action
        
        self.assertIn('Unsupported snapshot', str(ctx.exception))

    def test_build_actions_no_main_accounts_snapshot(self):
        system_account_names = ["init-0", "init-1", "init-2", "init-3", "init-4",
            "init-5", "init-6", "init-7", "init-8", "init-9", "init-10", "init-11",
            "init-12", "init-13", "init-14", "init-15", "init-16", "init-17",
            "init-18", "init-19", "init-20", "elect-0", "elect-1", "elect-2",
            "elect-3", "elect-4", "elect-5", "elect-6", "elect-7", "elect-8",
            "elect-9", "tnman", "porter"]
        
        shutil.copyfile("test-no-main-accounts-snapshot.json", "/tmp/test-no-main-accounts-snapshot.json")
        conf = FULL_CONF.copy()
        conf["snapshot_file"] = "/tmp/test-no-main-accounts-snapshot.json"
        
        for action in txgen.build_actions(conf):
            cmd, args = action
            
            if cmd == "submit_transaction":
                for type, value in args["tx"]["operations"]:
                    if type == 'account_create_operation':
                        new_account_name = value['new_account_name']
                        self.assertIn(new_account_name, system_account_names)
