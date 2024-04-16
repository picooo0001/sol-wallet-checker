from solders.keypair import Keypair
from discord_webhook import DiscordWebhook, DiscordEmbed
import requests
import json

# Load configuration from JSON file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

webhook_url = config['webhook_url']
API_KEY_ID = config['api_key_id']
API_SECRET_KEY = config['api_secret_key']

HEADERS = {
    "APIKeyID": API_KEY_ID,
    "APISecretKey": API_SECRET_KEY
}

name_input = str(input("Enter a keyword: "))
update_authority_input = input("Enter an update authority address: ")

input_filename = 'private_keys.txt'
output_filename = 'filtered_nfts.txt'

def get_pubkey(exported_pk):
    keypair = Keypair.from_base58_string(exported_pk)
    pk = str(keypair.pubkey())
    return pk

def send_discord_webhook_with_embed(name_input, name, pk, image_url, webhook_url):
    webhook = DiscordWebhook(url=webhook_url)
    embed = DiscordEmbed(title="Solana Wallet Checker - NFT found!", color="0ced48")
    embed.add_embed_field(name="Search term", value=name_input)
    embed.add_embed_field(name="Name", value=name)
    embed.add_embed_field(name="Wallet Address", value=pk, inline=False)
    embed.set_thumbnail(url=image_url)
    embed.set_footer(text="Picooo", icon_url="https://pbs.twimg.com/profile_images/1472933274209107976/6u-LQfjG_400x400.jpg")
    embed.set_timestamp()
    webhook.add_embed(embed)
    
    response = webhook.execute()
    if response.status_code != 200:
        print(f"Failed to send webhook with embed, status code {response.status_code}.")
    else:
        print("Webhook with embed sent successfully.")

def fetch_and_filter_nfts(exported_pk, name_input, update_authority_input, webhook_url):
    pk = get_pubkey(exported_pk)

    PARAMS = {
        "public_key": pk,
        "network": "mainnet-beta"
    }

    response = requests.get(
        "https://api.blockchainapi.com/v1/solana/wallet/nfts",
        params=PARAMS,
        headers=HEADERS
    )

    json_response = response.json()
    filtered_data = []
    found_match = False

    for nft in json_response.get('nfts_metadata', []):
        name = nft['data']['name']
        update_authority = nft['update_authority']
        image_url = nft['off_chain_data'].get('image', 'No image URL provided')

        if name_input in name or update_authority == update_authority_input:
            found_match = True 
            filtered_data.append({'name': name, 'wallet address': pk, 'update_authority': update_authority, 'image_url': image_url})
            print(f"Found {name} in {pk}")
            print("Sending webhook...")
            send_discord_webhook_with_embed(name_input, name, pk, image_url, webhook_url)

    if not found_match:
        print(f"No matching NFT found in {pk}")

    return filtered_data


with open(input_filename, 'r') as keys_file, open(output_filename, 'w') as output_file:
    for exported_pk in keys_file:
        exported_pk = exported_pk.strip()  
        filtered_data = fetch_and_filter_nfts(exported_pk, name_input, update_authority_input, webhook_url)
        for item in filtered_data:
            output_file.write(f"Name: {item['name']}, Wallet address: {item['wallet address']}, Update Authority: {item['update_authority']}\n")

print(f"Script checked all wallets.")
