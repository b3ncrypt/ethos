# import standard libraries and dependencies
import requests
import time
import csv
import argparse
import os
import networkx as nx
from datetime import datetime
import config 

# ascii art / details
VERSION = "Ethos V1"
CATCHPHRASE = "Illuminating the Ledger"

def print_banner():
    banner = f"""
        ______ _   _                 
       |  ____| | | |                
       | |__  | |_| |__   ___  ___   
       |  __| | __| '_ \\ / _ \\/ __|  
       | |____| |_| | | | (_) \\__ \\  
       |______|\\__|_| |_|\\___/|___/  
              {VERSION} - {CATCHPHRASE}
    """
    logo = """
                /\\
               /  \\
              /    \\
             |------|
              \\    /
               \\  /
                \\/
    """
    print(banner)
    print(logo)


# function to get contract label for an address using Etherscan API
def get_contract_label(address, api_key):
    url = "https://api.etherscan.io/v2/api"
    params = {"chainid": 1, "module": "contract", "action": "getsourcecode", "address": address, "apikey": api_key} # etherscan API endpoint and parameters to fetch contract source code and metadata for the given address
    try:
        time.sleep(0.2)
        res = requests.get(url, params=params).json()
        if res.get("status") == "1" and res["result"][0].get("ContractName"): #if api call is successful and contract name is available, return the contract name as label for the node in the graph
            return res["result"][0]["ContractName"]
    except:
        pass
    return "Unknown" # if no label is found or API call fails, return "Unknown" as default label for the node in the graph
# function to fetch transactions for a given address using Etherscan API
def fetch_transactions(address, api_key, limit):
    url = "https://api.etherscan.io/v2/api"
    params = {
        "chainid": 1, "module": "account", "action": "txlist", 
        "address": address, "page": 1, "offset": limit, 
        "sort": "desc", "apikey": api_key
    }
    # add a small delay to respect API rate limits and handle potential request failures
    try:
        time.sleep(0.3)
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except:
        return {}
# main function to run the trace and build the graph of transactions
def run_trace(target_address, max_hops, tx_limit):
    api_key = config.ETHERSCAN_API_KEY
    target_address = target_address.lower()
    
    # graph and data structures to hold nodes, edges, and visited status
    G = nx.DiGraph()
    visited_nodes = {} 
    all_edges = []
    total_eth_out = 0
# print banner and initial investigation details
    print_banner()
    print(f"[!] INVESTIGATION START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[!] Target Address: {target_address}")
    print(f"[!] Config: {max_hops} Hops | {tx_limit} Tx Limit per node\n")

    # initial fetch of target's transactions for first hop
    data = fetch_transactions(target_address, api_key, tx_limit)
    target_txs = data.get('result', [])
    print(f"[*] Initial Scan: Found {len(target_txs)} transactions leaving target.\n")
    # add target address as starting node with hop 0 and contract label
    visited_nodes[target_address] = {'hop': 0, 'label': get_contract_label(target_address, api_key), 'fresh': "False"}
    G.add_node(target_address, hop=0, label=visited_nodes[target_address]['label'], fresh="False")

    queue = [] # queue for BFS traversal of hops

    # process first hop transactions and queue next addresses
    for tx in target_txs:
        target = tx['to'].lower()
        if not target: continue
        val = int(tx['value']) / 10**18
        total_eth_out += val
        
        print(f"    [Link] Source -> {target[:12]}... | Amount: {val:.4f} ETH") # print outgoing transactions from target address with link and value details
        
        all_edges.append({'from': target_address, 'to': target, 'value': val, 'hash': tx['hash'], 'hop': 0}) # add edge details to list for CSV output
        G.add_edge(target_address, target, value=val, hash=tx['hash']) # add edge to graph with value and transaction hash as attributes
        
        if target not in visited_nodes: # queue next address for BFS if not already visited
            queue.append((target, 1))

    # BFS traversal for subsequent hops
    while queue:
        current_address, current_hop = queue.pop(0)
        if current_address in visited_nodes or current_hop > max_hops:
            continue
           # fetch transactions for the current address 
        data = fetch_transactions(current_address, api_key, tx_limit)
        transactions = data.get('result', [])
        # get contract label for current address and add to graph
        label = get_contract_label(current_address, api_key)
        visited_nodes[current_address] = {'hop': current_hop, 'label': label, 'fresh': "True"}
        G.add_node(current_address, hop=current_hop, label=label, fresh="True")

        print(f"\n[*] Processing Hop {current_hop}: {current_address[:14]}...")
        # process transactions for current address and queue next addresses
        for tx in transactions:
            target = tx['to'].lower()
            if not target: continue
            val = int(tx['value']) / 10**18
            
            # only outgoing transactions from current address
            all_edges.append({'from': current_address, 'to': target, 'value': val, 'hash': tx['hash'], 'hop': current_hop})
            G.add_edge(current_address, target, value=val, hash=tx['hash'])
            
            # queue next address if not visited and within hop limit
            if target not in visited_nodes:
                print(f"    [Link] {current_address[:8]}... -> {target[:8]}... | {val:.4f} ETH")
                queue.append((target, current_hop + 1))

    # save outputs and print final summary
    prefix = save_outputs(visited_nodes, all_edges, G, target_address)
    
    print("\n" + "="*50)
    print("--- FINAL INVESTIGATION SUMMARY ---")
    print(f"Total Unique Addresses Found: {len(visited_nodes)}") # total unique nodes in the graph
    print(f"Total Transactions Mapped:   {len(all_edges)}") # total edges in the graph
    print(f"Total ETH Flow from Target:  {total_eth_out:.4f} ETH") # total ETH value flowing out from the target address across all hops
    print("-" * 50) 
    print(f"Files Created in 'forensic_results/':") # list the output files generated with the prefix, target address and timestamp
    print(f" -> {prefix}_nodes.csv") # save nodes to CSV
    print(f" -> {prefix}_edges.csv") # save edges to CSV
    print(f" -> {prefix}_graph.gexf") # save graph in GEXF format
    print("="*50)
# helper function to save nodes, edges, and graph outputs to files
def save_outputs(nodes, edges, G, target_address):
    folder = "forensic_results"
    if not os.path.exists(folder): os.makedirs(folder) 
    timestamp = datetime.now().strftime("%Y%m%d_%H%M") 
    prefix = f"{target_address[:10]}_{timestamp}" # 
    path_prefix = f"{folder}/{prefix}"
# save nodes to CSV with address, hop, label, and freshness status
    with open(f"{path_prefix}_nodes.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['address', 'hop', 'label', 'fresh'])
        writer.writeheader()
        for addr, meta in nodes.items():
            writer.writerow({'address': addr, 'hop': meta['hop'], 'label': meta['label'], 'fresh': meta['fresh']})
    # save edges to CSV with source, target, value, transaction hash, and hop level
    with open(f"{path_prefix}_edges.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['from', 'to', 'value', 'hash', 'hop'])
        writer.writeheader()
        writer.writerows(edges)
# save graph in GEXF format for visualization in tools like Gephi
    nx.write_gexf(G, f"{path_prefix}_graph.gexf")
    return prefix
# entry point for command-line execution with argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ethos V1: Ethereum Forensic Tool") 
    parser.add_argument("-a", "--address", required=True, help="Target Wallet Address")
    parser.add_argument("-H", "--hops", type=int, default=3, help="Max Hops (default: 3)")
    parser.add_argument("-l", "--limit", type=int, default=20, help="Tx Limit per node (default: 20)")
    args = parser.parse_args()
    run_trace(args.address, args.hops, args.limit)