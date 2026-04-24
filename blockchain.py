import hashlib
import time
import json

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self):
        """
        A function that return the hash of the block contents.
        """
        # Exclude hash from the block representation for computing new hash
        block_rep = {k: v for k, v in self.__dict__.items() if k != 'hash'}
        block_string = json.dumps(block_rep, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        block = cls(data['index'], data['transactions'], data['timestamp'], data['previous_hash'])
        block.nonce = data.get('nonce', 0)
        block.hash = data.get('hash', block.compute_hash())
        return block

class Blockchain:
    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block(0, [], time.time(), "0")
        self.chain.append(genesis_block)

    def save_to_file(self, filename="blockchain_data.json"):
        """
        Saves the current chain to a JSON file.
        """
        chain_data = [block.to_dict() for block in self.chain]
        with open(filename, 'w') as f:
            json.dump({
                "chain": chain_data,
                "unconfirmed": self.unconfirmed_transactions
            }, f, indent=4)

    def load_from_file(self, filename="blockchain_data.json"):
        """
        Loads the chain from a JSON file if it exists.
        """
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.chain = [Block.from_dict(b) for b in data['chain']]
                self.unconfirmed_transactions = data.get('unconfirmed', [])
                return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of latest block
          in the chain match.
        """
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not self.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def is_valid_proof(self, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    @staticmethod
    def proof_of_work(block):
        """
        Function that tries different values of nonce to get a hash
        that satisfies our difficulty criteria.
        """
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def add_transaction(self, user, ev_model, duration, amount, tx_id):
        """
        Creates a new transaction and adds it to the unconfirmed list.
        Each transaction includes all fields required by the specification.
        """
        transaction = {
            "user": user,
            "ev_model": ev_model,
            "time": duration,
            "amount": amount,
            "transaction_id": tx_id,
            "timestamp": time.time(),
            "previous_hash": self.last_block.hash
        }
        self.unconfirmed_transactions.append(transaction)
        return True

    def add_new_transaction(self, transaction):
        # Compatibility with existing code if any
        self.unconfirmed_transactions.append(transaction)

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof of Work.
        """
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = []
        return new_block.index

# Difficulty for Proof of Work
Blockchain.difficulty = 2
