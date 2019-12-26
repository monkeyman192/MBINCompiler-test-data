#!/usr/bin/env bash
#
# Author: Stefan Buck
# License: MIT
# https://gist.github.com/stefanbuck/ce788fee19ab6eb0b4447a85fc99f447
#
# Contains modifications suggested by huxingyi:
# https://gist.github.com/stefanbuck/ce788fee19ab6eb0b4447a85fc99f447#gistcomment-2555516
# 
# This has been almost completely re-written by monkeyman192.
#
# This script accepts the following parameters:
#
# * owner
# * repo
# * filename
# * github_api_token
#
# Script to upload a release asset using the GitHub API v3.
#
# Example:
#
# upload-github-release-asset.sh github_api_token=TOKEN owner=stefanbuck repo=playground filename=./build.zip
#

# Check dependencies.
set -e
xargs=$(which gxargs || which xargs)

# Validate settings.
[ "$TRACE" ] && set -x

CONFIG=$@

for line in $CONFIG; do
  eval "$line"
done

# Get the version of the data
# This is the Steam Build ID
local_tag=$(cat ./data/.version)

# Define variables.
GH_API="https://api.github.com"
GH_REPO="$GH_API/repos/$owner/$repo"
# Always get the most recent release
GH_TAGS="$GH_REPO/releases/latest"
AUTH="Authorization: token $github_api_token"
WGET_ARGS="--content-disposition --auth-no-challenge --no-cookie"
CURL_ARGS="-LJO#"

# Validate token.
curl -o /dev/null -sH "$AUTH" $GH_REPO || { echo "Error: Invalid repo, token or network issue!";  exit 1; }

# Read asset tags.
response=$(curl -sH "$AUTH" $GH_TAGS)

# Get ID, tag name and asset id of the current release
id=$(echo "$response" | jq -r '.id')
latest_tag=$(echo "$response" | jq -r '.tag_name')
asset_id=$(echo "$response" | jq -r '.assets[0].id')

create_release()
# Function to create a new release
{
    curl \
    --user $owner:$github_api_token \
    --header "Accept: application/vnd.github.manifold-preview" \
    --data "{\"tag_name\":\"$local_tag\", \"body\":\"MBINCompiler test data for NMS Steam BuildID: $local_tag\"}" \
    "https://api.github.com/repos/$owner/$repo/releases?access_token=$github_api_token"
}

# First, check to see if the local tag is equal to the release tag
if [[ $local_tag == $latest_tag ]]
then
    # In this case we want to remove the most recent release and the tag associated with it
    curl -X DELETE -H "$AUTH" "https://api.github.com/repos/$owner/$repo/releases/$id"
    curl -X DELETE -H "$AUTH" "https://api.github.com/repos/$owner/$repo/refs/tags/$latest_tag"
    curl -X DELETE -H "$AUTH" "https://api.github.com/repos/$owner/$repo/releases/assets/$asset_id"
    # Then create a new release
    create_release
# Else, if the tag provided here is greater than the most recent release then create a new release
elif [[ $local_tag > $latest_tag ]]
then
    create_release
else
    # In this case we have a version number that is behind the current release on github
    echo "Provided version tag is behind the current releases"
    exit 1
fi

# Get the id of the new release so we can upload assets to it
response=$(curl -sH "$AUTH" $GH_TAGS)
release_id=$(echo "$response" | jq -r '.id')

# Upload asset
echo "Uploading asset... "

# Construct url
GH_ASSET="https://uploads.github.com/repos/$owner/$repo/releases/$release_id/assets?name=$(basename $filename)"
# And finally upload the file
curl --data-binary @"$filename" -H "$AUTH" -H "Content-Type: application/octet-stream" $GH_ASSET
