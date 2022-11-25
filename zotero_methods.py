import argparse
import os
import shutil
from typing import Dict

from pyzotero import zotero

LIBRARY_ID = "9263192"
API_KEY = "V5aS5zoDzicBTbujbxeM4OZn"

LOCAL_ZOTERO_PATH = "/Users/sebastianlee/Zotero/storage"
ZOTERO_PDFS_PATH = "/Users/sebastianlee/Dropbox/Zotero"

parser = argparse.ArgumentParser()

parser.add_argument("--num_items", type=int, default=10)
parser.add_argument("--debug", action="store_true")

"""
1. Make separate file for keys as above
2. Find out where pdf file is stored - is it just a pointer to a url 
   or is the pdf stored locally (I think so)?
3. Use attachment methods to link file
"""


def get_recent_items(zotero_instance: zotero.Zotero, num_items: int):
    return zotero_instance.items(limit=num_items)


def update_item(
    zotero_instance: zotero.Zotero, 
    item: Dict, 
    aux_info: Dict, 
    parent_keys: set,
    debug: bool
) -> Dict:

    if "linkMode" in item["data"]:
        if item["data"]["linkMode"] == "imported_url":
            
            has_parent = "parentItem" in item["data"]
            if has_parent:
                parent_id = item["data"]["parentItem"]
                filename = item["data"]["filename"]

                path_to_file = os.path.join(LOCAL_ZOTERO_PATH, item["key"], filename)
                shutil.copy(path_to_file, ZOTERO_PDFS_PATH)
                
                # delete item
                if not debug:
                    zotero_instance.delete_item(item)

                aux_info_entry = {"filename": filename}
                aux_info[parent_id] = aux_info_entry

                parent_keys.add(parent_id)
        
        elif item["data"]["linkMode"] == "linked_file":
            parent_id = item["data"]["parentItem"]
            aux_info[parent_id] = None

            parent_keys.add(parent_id)

    else:
        if item["key"] in aux_info:
            if aux_info[item["key"]] is not None:
                item_template = zotero_instance.item_template(itemtype="attachment", linkmode="linked_file")
                filename = aux_info[item["key"]]["filename"]
                item_template["title"] = filename
                item_template["path"] = f"attachments:{filename}"
                if not debug:
                    zotero_instance.create_items([item_template], parentid=item["key"])
        else:
            pass
    
    return aux_info, parent_keys


if __name__ == "__main__":

    args = parser.parse_args()

    # we now have a Zotero object, zot, and access to all its methods
    zot = zotero.Zotero(LIBRARY_ID, 'user', API_KEY)

    recent_items = get_recent_items(zotero_instance=zot, num_items=2 * args.num_items)

    aux_info = {}
    parent_keys = set()
    item_index = 0

    while len(parent_keys) <= args.num_items:
        import pdb; pdb.set_trace()
        aux_info, parent_keys = update_item(
            zotero_instance=zot,
            item=recent_items[item_index],
            aux_info=aux_info,
            parent_keys=parent_keys,
            debug=args.debug
        )
        item_index += 1
