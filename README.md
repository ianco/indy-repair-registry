
# Indy Repair Revocation Registry

Repair a "broken" revocation registry - this can happen if the eldger write fails during a credential revocation, in which case the wwallet is updated and te ledger isn't.  If this happens no more credentials can be revoked against a registry.

This script will repair the problem by calculating the new accumulator and writing it to the ledger, getting the ledger and wallet back in sync.

## Running the repair script

In a local bash shell:

```bash
git clone https://github.com/ianco/indy-repair-registry.git
cd indy-repair-registry
virtualenv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

You need to edit the script to set your environment:

- genesis transactions (for your ledger)
- id of your revocation registry
- index of each revoked transaction

Once you have updated the script:

```bash
python recover.py
```
