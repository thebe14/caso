#!/usr/bin/sh

if [ -z "$1" ]; then
    echo "New version not given";
    exit 1;
fi

VERSION=$1

echo "# I'm not running anything, run this by yourself"

last=`git tag -l|tail -n1`

echo git-dch \
    --release \
    --new-version=$VERSION \
    --since=\"$last\" \
    --commit \
    --verbose 

echo git tag -s $VERSION

echo python setup.py sdist upload

echo mkdir /tmp/BUILD

echo
echo "# Debian packages"
echo cp dist/caso-${VERSION}.tar.gz /tmp/BUILD/caso_${VERSION}.orig.tar.gz
echo cd /tmp/BUILD
echo tar zxfv caso_${VERSION}.orig.tar.gz
echo debuild -S -sa
