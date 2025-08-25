import json
import os
import requests
import argparse
import time
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

MODEL_RPM = {
    "Gemini 2.5 Pro": 5,
    "Gemini 2.5 Flash": 10,
    "Gemini 2.5 Flash-Lite": 15,
    "Gemini 2.0 Flash": 15,
    "Gemini 2.0 Flash-Lite": 30,
}

CHECKPOINT_FILE_SUFFIX = '.checkpoint.json'


def load_env():
    env_path = Path(__file__).resolve().parent / '.env'
    load_dotenv(dotenv_path=env_path)
    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL_NAME')
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in .env")
    if not model_name:
        raise RuntimeError("GEMINI_MODEL_NAME not set in .env")
    return api_key, model_name


def build_endpoint_url(model_name):
    base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    model_url_part = model_name.lower().replace(' ', '-')
    return f"{base_url}/{model_url_part}:generateContent"


def get_wait_time(model_name):
    rpm = MODEL_RPM.get(model_name, 5)
    return 60.0 / rpm


def collect_folders(node, parent_path="", folders=None):
    if folders is None:
        folders = {}
    if node.get('type') == 'text/x-moz-place-container':
        path = f"{parent_path}/{node['title']}" if parent_path else node['title']
        folders[path] = node['id']
        for child in node.get('children', []):
            collect_folders(child, path, folders)
    return folders


def collect_tags(node, tags=None):
    if tags is None:
        tags = set()
    if node.get('type') == 'text/x-moz-place' and 'tags' in node:
        for tag in node['tags'].split(','):
            tags.add(tag.strip())
    for child in node.get('children', []):
        collect_tags(child, tags)
    return tags


def find_node_by_id(node_list, target_id):
    for node in node_list:
        if node['id'] == target_id:
            return node
        if node.get('children'):
            found = find_node_by_id(node['children'], target_id)
            if found:
                return found
    return None


def classify_bookmark(bookmark, current_folder, folders, all_tags, api_key, endpoint):
    prompt = (
        f"Bookmark:\n"
        f" Title: {bookmark['title']}\n"
        f" URL: {bookmark['uri']}\n"
        f" Current folder: {current_folder or 'unfiled'}\n"
        f"Existing folders:\n"
        + "\n".join(f" - {name}" for name in folders.keys()) + "\n"
        f"Existing tags:\n"
        + "\n".join(f" - {tag}" for tag in sorted(all_tags)) + "\n\n"
        "Instructions:\n"
        " 1. Do NOT remove or change any tags that already exist on the bookmark.\n"
        " 2. Prefer assigning the bookmark to one of the EXISTING folders, if relevant.\n"
        " 3. Only suggest a NEW folder if none of the existing folders appropriately fit.\n"
        " 4. If suggesting a new folder, base its name on the CURRENT folder where the bookmark is located.\n"
        " 5. Only suggest NEW tags if none of the existing tags apply to the url.\n"
        " 6. For new tags, consider the current folder and bookmark content as context.\n"
        " 7. Ensure at the end, each bookmark has at least ONE tag, either existing or new.\n"
        "Return a JSON object with exactly these fields:\n"
        " - folder: name of chosen existing folder, or empty string if none.\n"
        " - tags: comma-separated list of existing tags to add, or empty if none.\n"
        " - new_folder: suggested new folder name if no existing folder was chosen, otherwise empty.\n"
        " - new_tags: comma-separated list of suggested new tags, otherwise empty.\n"
    )

    body = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json", "X-goog-api-key": api_key}
    resp = requests.post(endpoint, json=body, headers=headers)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]


def save_checkpoint(data, original_path):
    checkpoint_path = Path(original_path).with_suffix(CHECKPOINT_FILE_SUFFIX)
    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_bookmarks(file_path):
    checkpoint_path = Path(file_path).with_suffix(CHECKPOINT_FILE_SUFFIX)
    if checkpoint_path.exists():
        print(f"Found checkpoint at {checkpoint_path}. Resuming from checkpoint.")
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            return json.load(f), checkpoint_path
    else:
        print(f"No checkpoint found, loading original bookmarks from {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f), None


def main():
    parser = argparse.ArgumentParser(description="Sort Firefox bookmarks via Gemini API")
    parser.add_argument('-f', '--file', required=True, help="Path to Firefox bookmarks JSON file")
    args = parser.parse_args()

    api_key, model_name = load_env()
    endpoint = build_endpoint_url(model_name)
    wait_time = get_wait_time(model_name)

    data, checkpoint_path = load_bookmarks(args.file)

    unfiled_node = next(n for n in data['children'] if n['title'] == 'unfiled')
    folders = collect_folders(unfiled_node)
    all_tags = collect_tags(data)

    unsorted = [
        b for b in unfiled_node.get('children', [])
        if b['type'] == 'text/x-moz-place' and not b.get('processed')
    ]

    if not unsorted:
        print("No bookmarks to process.")
        return

    print(f"Processing {len(unsorted)} bookmarks...")

    with tqdm(unsorted, desc="Classifying bookmarks", unit="bookmark") as pbar:
        for bm in pbar:
            current_folder = 'unfiled'

            try:
                res = classify_bookmark(bm, current_folder, folders, all_tags, api_key, endpoint)
                if isinstance(res, str):
                    result = json.loads(res)
                else:
                    result = res
            except Exception as e:
                print(f"\nError processing bookmark '{bm.get('title', '')}': {e}")
                print("Saving checkpoint and exiting to allow resume.")
                save_checkpoint(data, args.file)
                return

            folder = result.get('folder') or ''
            new_folder = result.get('new_folder') or ''
            existing_tags = [t.strip() for t in result.get('tags', '').split(',') if t.strip()]
            new_tags = [t.strip() for t in result.get('new_tags', '').split(',') if t.strip()]

            created_folder_msg = None
            created_tags_msg = None

            if folder:
                target_folder = folder
            elif new_folder:
                target_folder = new_folder
                if new_folder not in folders:
                    new_id = str(max(int(x) for x in folders.values()) + 1)
                    folders[new_folder] = new_id
                    unfiled_node['children'].append({
                        'guid': None,
                        'title': new_folder,
                        'typeCode': 2,
                        'type': 'text/x-moz-place-container',
                        'id': int(new_id),
                        'children': []
                    })
                    created_folder_msg = new_folder
            else:
                target_folder = current_folder

            # Remove bookmark from unfiled children
            unfiled_node['children'] = [c for c in unfiled_node['children'] if c is not bm]

            parent = find_node_by_id(data['children'], folders.get(target_folder))
            if parent is None:
                print(f"Warning: Folder with id {folders.get(target_folder)} not found; placing back into 'unfiled'")
                unfiled_node['children'].append(bm)
            else:
                parent.setdefault('children', []).append(bm)

            old_tags = [t.strip() for t in bm.get('tags', '').split(',') if t.strip()]
            final_tags = set(old_tags)
            for t in existing_tags:
                final_tags.add(t)
            for t in new_tags:
                final_tags.add(t)

            if not final_tags:
                final_tags.add("untagged")
            if new_tags:
                created_tags_msg = ", ".join(new_tags)

            bm['tags'] = ','.join(sorted(final_tags))
            bm['processed'] = True

            postfix = {}
            if created_folder_msg:
                postfix["New Folder"] = created_folder_msg
            if created_tags_msg:
                postfix["New Tags"] = created_tags_msg

            pbar.set_postfix(postfix, refresh=False)
            save_checkpoint(data, args.file)
            time.sleep(wait_time)

    out_path = Path(args.file).with_name('Fox-bookmarks-sorted.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    checkpoint_file = Path(args.file).with_suffix(CHECKPOINT_FILE_SUFFIX)
    if checkpoint_file.exists():
        checkpoint_file.unlink()

    print(f"\nProcessing complete. Saved sorted bookmarks to {out_path}")


if __name__ == '__main__':
    main()
