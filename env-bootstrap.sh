set -eu

# list of private libs
elixr_base_url=https://bitbucket.org/hazeltek-dev/elixr.base/get/v0.4.tar.gz
elixr_base_pth=.tox/elixr.base.tar.gz

# locate target .tox environments
echo "Processing..."
result=$(cat tox.ini | grep -ioE 'py\d+');

# download external package into .tox
if [ ${#result} -gt 0 ] && [ ! -f ${elixr_base_pth} ]; then
    echo >&1 "Downloading 'elixr.base' from private repository..."
    curl --user ${REPO_USERNAME}:${APP_PASSWORD} -X GET $elixr_base_url > $elixr_base_pth;
fi

# ${#result} provides length of matched string
if [ ${#result} -gt 0 ]; then
    echo "Match found: $(echo ${result})"
    for i in $(echo ${result} | tr " " "\n")
    do
        .tox/$i/bin/pip install $elixr_base_pth;
        .tox/$i/bin/pip install .
    done
fi
