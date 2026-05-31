# -*- coding: utf-8 -*-
import os
import sys
import requests
import subprocess

def get_github_token():
    try:
        p = subprocess.Popen(['git', 'credential', 'fill'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = p.communicate("url=https://github.com\n\n")
        username = None
        password = None
        for line in stdout.splitlines():
            if line.startswith("username="):
                username = line.split("=", 1)[1].strip()
            elif line.startswith("password="):
                password = line.split("=", 1)[1].strip()
        return username, password
    except Exception as e:
        print("Failed to read git credentials:", e)
        return None, None

def publish_to_github():
    repo = "topcatai/VantageMail"
    tag = "v1.0.1"
    
    username, token = get_github_token()
    if not token:
        print("Error: Could not retrieve GitHub token from Git Credential Manager.")
        sys.exit(1)
        
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 1. Check if release already exists
    print("Checking if release exists on GitHub...")
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    r = requests.get(url, headers=headers)
    
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
            "body": "Vantage Mail v1.0.1 bugfix release.\n\nChanges:\n- Clean settings and data cache on uninstallation.\n- Live folder unread badges.\n- Modeless email viewer and drafts auto-save.\n- SMTP and IMAP connection optimizations.",
            "draft": False,
            "prerelease": False
        }
        create_url = f"https://api.github.com/repos/{repo}/releases"
        r = requests.post(create_url, headers=headers, json=payload)
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
            asset_id = asset["id"]
            del_url = f"https://api.github.com/repos/{repo}/releases/assets/{asset_id}"
            del_r = requests.delete(del_url, headers=headers)
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
    
    upload_url = f"https://uploads.github.com/repos/{repo}/releases/{release_id}/assets"
    
    headers["Content-Type"] = "application/octet-stream"
    
    with open(file_path, "rb") as f:
        upload_r = requests.post(
            upload_url,
            headers=headers,
            params={"name": file_name},
            data=f
        )
        
    if upload_r.status_code in (200, 201):
        print("MSI asset uploaded successfully to GitHub!")
    else:
        print(f"Failed to upload asset: {upload_r.status_code} - {upload_r.text}")
        sys.exit(1)

if __name__ == '__main__':
    publish_to_github()
