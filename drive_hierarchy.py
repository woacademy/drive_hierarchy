#!/usr/bin/env python3
'''
drive_hierarchy.py
Google Drive - Hierarchy

Last updated 16/02/2018
'''
import os
import json
import httplib2

# Powered by google-api-python-client.
from natsort import natsorted
from apiclient import discovery
from oauth2client import tools
from oauth2client import client
from oauth2client.file import Storage

# API access definitions.
APP_NAME = "drive_hierarchy"
DRIVE_FOLDER = ""
DRIVE_FOLDERID = ""
SCOPE = "https://www.googleapis.com/auth/drive.metadata.readonly"

# Local files.
OUTPUT_FILE = f"{APP_NAME}.json"
SECRET_FILE = "client_secret.json"


def get_credentials():
    '''
    Google's get_credentials OAuth example.
    @see developers.google.com/drive/v3/web/quickstart/python

    @noreturn
    '''
    home = os.path.expanduser("~")
    location = os.path.join(home, ".credentials")
    if not os.path.exists(location):
        os.makedirs(location)

    # Try to load credentials from file.
    credentials = os.path.join(location, f".{APP_NAME}")
    store = Storage(credentials)
    auth = store.get()
    if not auth or auth.invalid:
        # Google OAuth magic.
        flow = client.flow_from_clientsecrets(SECRET_FILE, SCOPE)
        flow.user_agent = APP_NAME
        auth = tools.run_flow(flow, store)

    return auth


def process_hierarchy(service, hierarchy, parent):
    '''
    Retrieve a hierarchy's contents.
    @see Use recursively.

    @param service      API interaction resource to use.
    @param hierarchy    Hierarchy dictionary at current position.
    @param parent       Current folder to fetch.
    @noreturn
    '''
    query = service.files().list(q=f"parents in '{parent}'",
                                 fields="files(mimeType, id, name)").execute()

    # Return on completely empty folders.
    results = query.get("files", [])
    if not results:
        return

    for key in results:
        if "folder" in key["mimeType"]:
            # Recurse through subfolders.
            hierarchy.setdefault("children", []).append({
                "id": key["id"],
                "name": key["name"],
                "files": [],
                "children": []
            })
            process_hierarchy(service, hierarchy["children"][-1], key["id"])
        else:
            # Use the setdefault() method to append files.
            hierarchy.setdefault("files", []).append({
                "id": key["id"],
                "name": key["name"]
            })


def sort_hierarchy(hierarchy):
    '''
    Sort a folder's contents.
    @see Use recursively.

    @param hierarchy    Hierarchy dictionary at current position.
    @noreturn
    '''
    if hierarchy["files"]:
        # Sort files by display name.
        hierarchy["files"] = natsorted(hierarchy["files"],
                                       key=lambda k: k["name"])

    if hierarchy["children"]:
        # Sort subfolders by display name too.
        hierarchy["children"] = natsorted(hierarchy["children"],
                                          key=lambda k: k["name"])

        # Sort the hierarchy recursively.
        for child in hierarchy["children"]:
            sort_hierarchy(child)


def main():
    '''
    Authenticate with Google Drive through oAuth, construct a file hierarchy
    for the DRIVE_FOLDER folder and ouput it in JSON format.

    @noreturn
    '''
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build("drive", "v3", http=http)

    # defaultdict(list) behaves weirdly here, use a generic one.
    hierarchy = {
        "id": DRIVE_FOLDERID,
        "name": DRIVE_FOLDER,
        "files": [],
        "children": []
    }
    process_hierarchy(service, hierarchy, DRIVE_FOLDERID)
    sort_hierarchy(hierarchy)

    # Output in JSON format.
    with open(OUTPUT_FILE, "w") as file:
        json.dump(hierarchy, file)

# Avoid main() being executed during import.
if __name__ == "__main__":
    main()
