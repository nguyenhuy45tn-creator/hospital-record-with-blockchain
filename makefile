ganache:
	ganache --database.dbPath chain --wallet.mnemonic "spatial draw combine river drive average bomb much riot brick prevent clog" 

example:
	mox run example_importing --network ganache --private-key "0x9db892b6ddbdc723db979a80e68a93d4649a3c416f5ce1c145f358b3b895880f"
	mox run logger_demo.py --network ganache --private-key "0x9db892b6ddbdc723db979a80e68a93d4649a3c416f5ce1c145f358b3b895880f"

test:
	mox test

test-ganache:
	mox test
