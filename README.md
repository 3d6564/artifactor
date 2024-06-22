# artifactor

Help capture artifacts from remote hosts. The intent is a lightweight, parallelized tool that allows pulling artifact type information. The tool has basic flexibility to store new and additional commands in JSON format, please refer to `commands.json.template`.

## Supported features

- Add and store commands
- Add and store hosts
- Use a jumpbox for each connection
- Use password/key for each connection (password has limited testing)
- Parallelized connections to each host

## TODO

- [ ] Restructure rest of utils folder
- [ ] add more linux commands
- [ ] add better windows capability
- [ ] add more state awareness with classes