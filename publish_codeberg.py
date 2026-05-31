# -*- coding: utf-8 -*-
import os
import sys
import requests

def publish_to_codeberg():
    repo = "topcatai/VantageMail"
    tag = "v1.0.1"
    
    # Prompt the user for the Codeberg token
    print("Please retrieve a Personal Access Token from Codeberg (Settings -> Applications -> Generate Token).")
    token = input("Enter Codeberg Personal Access Token: ").strip()
    if not token:
        print("Error: Token cannot be empty.")
        sys.exit(1)
        
    headers = {
        "Authorization": f"token {token}",
        "accept": "application/json"
    }
    
    # 1. Check if release already exists
    print("Checking if release exists on Codeberg...")
    r = requests.get(f"https://codeberg.org/api/v1/repos/{repo}/releases/tags/{tag}", headers=headers)
    
    if r.status_code == 200:
        release_data = r.json()
        print("Found existing release.")
    elif r.status_code == 404:
        # Create release
        print("Release not found. Creating a new release...")
        payload = {
            "tag_name": tag,
            "target_commitish": "main",
            "name": f"Vantage Mail {tag}",
            "body": "Vantage Mail v1.0.1 bugfix release.\n\nChanges:\n- Email download batching (sync in chunks of 100)\n- Modeless window lifetime / button locking issues fixed\n- Start Menu shortcut icon integration (BMP-based .ico)",
            "draft": False,
            "prerelease": False
        }
        r = requests.post(f"https://codeberg.org/api/v1/repos/{repo}/releases", headers=headers, json=payload)
        if r.status_code not in (200, 201):
            print(f"Failed to create release: {r.status_code} - {r.text}")
            sys.exit(1)
        release_data = r.json()
        print("Release created successfully.")
    else:
        print(f"Failed to check release: {r.status_code} - {r.text}")
        sys.exit(1)
        
    release_id = release_data["id"]
    
    # Check if there are already assets we need to delete/overwrite
    for asset in release_data.get("assets", []):
        if asset["name"] == "vantage-mail-1.0.1-win64.msi":
            print("Found existing asset. Deleting old asset...")
            del_r = requests.delete(f"https://codeberg.org/api/v1/repos/{repo}/releases/{release_id}/assets/{asset['id']}", headers=headers)
            if del_r.status_code not in (200, 204):
                print(f"Warning: failed to delete old asset: {del_r.text}")
            else:
                print("Old asset deleted successfully.")
                
    # 2. Upload the new asset
    file_path = r"C:\aiproject\Goose\outlook_client\dist\vantage-mail-1.0.1-win64.msi"
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)
        
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    print(f"Uploading {file_name} ({file_size} bytes) to release...")
    
    url = f"https://codeberg.org/api/v1/repos/{repo}/releases/{release_id}/assets"
    
    with open(file_path, "rb") as f:
        files = {
            "attachment": (file_name, f)
        }
        params = {"name": file_name}
        upload_r = requests.post(url, headers=headers, files=files, params=params)
        
    if upload_r.status_code in (200, 201):
        print("MSI asset uploaded successfully to Codeberg!")
    else:
        print(f"Failed to upload asset: {upload_r.status_code} - {upload_r.text}")
        sys.exit(1)

if __name__ == '__main__':
    publish_to_codeberg()
