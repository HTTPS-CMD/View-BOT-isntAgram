import json

accounts_file = "data/accounts.json"
proxies_file = "data/proxies.txt"

def assign_proxies_to_accounts(acc_file= accounts_file , pro_file= proxies_file):
    # Load accounts
    with open(accounts_file, "r") as f:
        accounts = json.load(f)

    # Load proxies
    with open(proxies_file, "r") as f:
        proxies = [line.strip() for line in f if line.strip()]

    # Assign proxies to accounts
    for i, account in enumerate(accounts):
        if i < len(proxies):
            account["proxy"] = proxies[i]
        else:
            account["proxy"] = None  # If not enough proxies

    # Save updated accounts
    with open(accounts_file, "w") as f:
        json.dump(accounts, f, indent=2)

    print(f"✅ Assigned {len(proxies)} proxies to {len(accounts)} accounts.")
