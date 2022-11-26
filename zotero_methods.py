import argparse
import os
import shutil
from typing import Dict, List, Tuple

from pyzotero import zotero

LIBRARY_ID = "9263192"
API_KEY = "V5aS5zoDzicBTbujbxeM4OZn"

LOCAL_ZOTERO_PATH = "/Users/sebastianlee/Zotero/storage"
ZOTERO_PDFS_PATH = "/Users/sebastianlee/Dropbox/Zotero"

parser = argparse.ArgumentParser()

parser.add_argument("--num_items", type=int, default=5)
parser.add_argument("--debug", action="store_true")


def _copy_item_data_to_path(item: Dict) -> None:
    filename = item["data"]["filename"]
    path_to_file = os.path.join(LOCAL_ZOTERO_PATH, item["key"], filename)
    shutil.copy(path_to_file, ZOTERO_PDFS_PATH)

def _create_linked_file(zotero_instance, item: Dict, debug: bool) -> None:
    item_template = zotero_instance.item_template(itemtype="attachment", linkmode="linked_file")
    filename = aux_info[item["key"]]["filename"]
    item_template["title"] = filename
    item_template["path"] = f"attachments:{filename}"
    if not debug:
        zotero_instance.create_items([item_template], parentid=item["key"])

def update_item(
    zotero_instance: zotero.Zotero, 
    item: Dict, 
    aux_info: Dict, 
    parent_keys: set,
    debug: bool
) -> Dict:

    if "linkMode" in item["data"]:
        if item["data"]["linkMode"] == "imported_url":
            
            parent_id = item["data"].get("parentItem")
            if parent_id is not None:
                _copy_item_data_to_path(item=item)
                
                # delete item
                if not debug:
                    zotero_instance.delete_item(item)

                aux_info_entry = {"filename": item["data"]["filename"]}
                aux_info[parent_id] = aux_info_entry

                parent_keys.add(parent_id)
        
        elif item["data"]["linkMode"] == "linked_file":
            parent_id = item["data"]["parentItem"]
            aux_info[parent_id] = None

            parent_keys.add(parent_id)

    else:
        if item["key"] in aux_info:
            if aux_info[item["key"]] is not None:
                _create_linked_file(zotero_instance=zotero_instance, item=item, debug=debug)
        else:
            pass
    
    return aux_info, parent_keys


def _group_items(items: List) -> Dict[str, Tuple]:
    """(py)zotero defines separate item objects for parent and child items.
    This method groups such item pairs.
    
    Args:
        items: list of pyzotero items
    
    Returns:
        grouped_items: dictionary where key is parent item ID, 
        and value is list of items (including parent) that are 
        child instances of parent item. 
    """
    grouped_items = {}
    for item in items:
        parent_id = item["data"].get("parentItem")
        if parent_id is not None:
            if parent_id in grouped_items:
                grouped_items[parent_id].append(item)
            else:
                grouped_items[parent_id] = [item]
        else:
            if item["key"] in grouped_items:
                grouped_items[item["key"]].append(item)
            else:
                grouped_items[item["key"]] = [item]
    return grouped_items

if __name__ == "__main__":

    args = parser.parse_args()

    # we now have a Zotero object, zot, and access to all its methods
    zot = zotero.Zotero(LIBRARY_ID, 'user', API_KEY)

    # note this method call will include items in the bin
    recent_items = zot.items(limit=2 * args.num_items)
    grouped_items = _group_items(recent_items)

    aux_info = {}
    parent_keys = set()
    item_index = 0

    while len(parent_keys) < args.num_items:
        aux_info, parent_keys = update_item(
            zotero_instance=zot,
            item=recent_items[item_index],
            aux_info=aux_info,
            parent_keys=parent_keys,
            debug=args.debug
        )
        item_index += 1
