"""Recover a revocation registry."""

import asyncio
import hashlib
import tempfile
import time

import aiohttp
import base58

from indy_credx import (
    RevocationRegistry,
    RevocationRegistryDefinition,
    RevocationRegistryDelta,
)
from indy_vdr import open_pool, ledger


async def fetch_txns(genesis_path, registry_id):
    pool = await open_pool(genesis_path)
    print("Connected to pool")

    print("Fetch registry:", registry_id)
    fetch = ledger.build_get_revoc_reg_def_request(None, registry_id)
    result = await pool.submit_request(fetch)
    if not result["data"]:
        print("Registry definition not found")
        return
    data = result["data"]
    data["ver"] = "1.0"
    defn = RevocationRegistryDefinition.load(data)
    print("Tails URL:", defn.tails_location)

    async with aiohttp.ClientSession() as session:
        data = await session.get(defn.tails_location)
        tails_data = await data.read()
        tails_hash = base58.b58encode(hashlib.sha256(tails_data).digest()).decode(
            "utf-8"
        )
        if tails_hash != defn.tails_hash:
            print("Tails hash mismatch:", tails_hash, defn.tails_hash)
            return
        else:
            print("Checked tails hash:", tails_hash)
        tails_temp = tempfile.NamedTemporaryFile(delete=False)
        tails_temp.write(tails_data)
        tails_temp.close()

    to_timestamp = int(time.time())
    fetch = ledger.build_get_revoc_reg_delta_request(
        None, registry_id, None, to_timestamp
    )
    result = await pool.submit_request(fetch)
    if not result["data"]:
        print("Error fetching delta")
        return None

    accum_to = result["data"]["value"]["accum_to"]
    accum_to["ver"] = "1.0"
    delta = RevocationRegistryDelta.load(accum_to)
    registry = RevocationRegistry.load(accum_to)
    print("Ledger registry state:", registry.to_json())
    revoked = set(result["data"]["value"]["revoked"])
    print("Ledger revoked indexes:", revoked)

    return defn, registry, delta, revoked, tails_temp


def run(genesis_path, registry_id, set_revoked):
    ledger_data = asyncio.run(fetch_txns(genesis_path, registry_id))
    if not ledger_data:
        return
    defn, registry, delta, prev_revoked, tails_temp = ledger_data

    set_revoked = set(set_revoked)
    mismatch = prev_revoked - set_revoked
    if mismatch:
        print(
            "One or more credential indexes marked revoked on the ledger, but not in the new state:",
            mismatch,
        )

    updates = set_revoked - prev_revoked
    if not updates:
        print("No updates to perform")
    else:
        print("New revoked indexes:", updates)

        print("tails_temp:", tails_temp.name)
        update_registry = registry.copy()
        new_delta = update_registry.update(defn, [], updates, tails_temp.name)

        print("New delta:")
        print(new_delta.to_json())


if __name__ == "__main__":
    run(
        "genesis.txn",
        "KJKW5xiNXeGHLhXeMwH1pk:4:KJKW5xiNXeGHLhXeMwH1pk:3:CL:39610:default:CL_ACCUM:ec631ced-b985-403f-bdad-e7f2da219660",
        [1, 3, 5, 6],
    )
