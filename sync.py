"""
该模块用于在 GitHub 发布新 Release 时，同步上传到 Gitee 上
"""

import argparse
import os
import requests

parser = argparse.ArgumentParser(
    description="a script to sync GitHub Release to Gitee release."
)
parser.add_argument(
    "-t", "--tag", type=str, help="version tag of GitHub Release", required=True
)
args = parser.parse_args()

GITEE_OWNER = os.environ["GITEE_OWNER"]
GITEE_REPO = os.environ["GITEE_REPO"]
GITEE_USERNAME = os.environ["GITEE_USERNAME"]
GITEE_PASSWORD = os.environ["GITEE_PASSWORD"]
GITEE_CLIENT_ID = os.environ["GITEE_CLIENT_ID"]
GITEE_CLIENT_SECRET = os.environ["GITEE_CLIENT_SECRET"]

ACCESS_TOKEN = requests.post(
    "https://gitee.com/oauth/token",
    data={
        "grant_type": "password",
        "username": GITEE_USERNAME,
        "password": GITEE_PASSWORD,
        "client_id": GITEE_CLIENT_ID,
        "client_secret": GITEE_CLIENT_SECRET,
        "scope": "projects",
    },
).json()["access_token"]

TAG_NAME = args.tag
NAME = TAG_NAME
BODY = f"Seraphine {TAG_NAME}"
TARGET_COMMITISH = "main"
FILE_PATH = "Seraphine.zip"

HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}


def create_new_release(owner, repo):
    url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/releases"
    data = {
        "tag_name": TAG_NAME,
        "name": NAME,
        "body": BODY,
        "target_commitish": TARGET_COMMITISH,
    }
    response = requests.post(url, data=data, headers=HEADERS, timeout=30)
    if 200 <= response.status_code < 300:
        return response.json()["id"]
    else:
        print(response.json())
        raise requests.HTTPError("create release on gitee failed.")


def upload_file(onwer, repo, release_id):
    url = f"https://gitee.com/api/v5/repos/{onwer}/{repo}/releases/{release_id}/attach_files"
    files = {"file": open(FILE_PATH, "rb")}
    response = requests.post(url, files=files, headers=HEADERS, timeout=30)

    if 200 <= response.status_code < 300:
        return response.json()["browser_download_url"]
    else:
        print(response.json())
        raise requests.HTTPError("push release file to Gitee failed.")


release_id = create_new_release(GITEE_OWNER, GITEE_REPO)
download_url = upload_file(release_id)
print(
    f"latest GitHub Release has been synced to Gitee Release, download url is {download_url}"
)
