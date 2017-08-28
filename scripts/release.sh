#!/usr/bin/env bash

set -e

REMOTE=${1:-origin}

CURRENT_TAG=$(git tag | sort -nr | head -1 | sed 's/^v//')

CURRENT_MAJOR=$(echo $CURRENT_TAG | cut -d'.' -f1)
CURRENT_MINOR=$(echo $CURRENT_TAG | cut -d'.' -f2)
CURRENT_RELEASE=$(echo $CURRENT_TAG | cut -d'.' -f3)

NEXT_RELEASE=$(expr $CURRENT_RELEASE + 1)
NEXT_TAG="${CURRENT_MAJOR}.${CURRENT_MINOR}.${NEXT_RELEASE}"

sed -i "/^version/s/$CURRENT_TAG/$NEXT_TAG/g" templates/vars.yaml
sed -i "/version/s/$CURRENT_TAG/$NEXT_TAG/g" couchdiscover/__init__.py
sed -i "/VERSION/s/$CURRENT_TAG/$NEXT_TAG/g" Dockerfile
inv templates

git add .
git commit -m "Tag for release: $NEXT_TAG ..."

echo "Incrementing version $CURRENT_TAG > $NEXT_TAG ..."
git tag v$NEXT_TAG

echo "Pushing to github remote: $REMOTE ..."
git push $REMOTE master --tags
