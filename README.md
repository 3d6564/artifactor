# artifactor

Help capture artifacts from remote hosts. The intent is a lightweight, parallelized tool that allows pulling artifact type information. The tool has basic flexibility to store new and additional commands in JSON format, please refer to `commands.json.template`.

## Supported features

- Add and store commands
- Add and store hosts
- Use a jumpbox for each connection
- Use password/key for each connection (password has limited testing)
- Parallelized connections to each host

## Setup

Download the repository to your local device and make sure you have python install. Once it is downloaded, make sure to retrieve the required packages.

```sh
# clone the repo from online
git clone https://github.com/3d6564/artifactor.git

# install required libraries from requirements.txt
pip install -r ./artifactor/requirements.txt
```

As long as Python is setup in your `PATH` you should be able to start it with the below.

```sh
# change to the artifactor directory
cd ./artifactor

# run artifactor, it will initialize if first time
python artifactor
```

## TODO

- [ ] Restructure rest of utils folder
- [ ] add more linux commands
- [ ] add better windows capability
- [ ] add more state awareness with classes