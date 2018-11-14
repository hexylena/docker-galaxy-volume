# Galaxy Docker Volume

## Installation

Create a 'galaxy' spec file in `/etc/docker/plugins/galaxy.spec` containing:

```
tcp://localhost:8123
```

In this directory, to launch the server process, run:

```
make
```

## Running

```
make
```


## Usage

```
$ docker run -it --user 1000:1000 --mount type=volume,destination=/galaxy,volume-driver=galaxy,volume-opt=url=http://localhost,volume-opt=apikey=76d1a621e9d80751c1475c176ae6ee12 python:3.6-alpine /bin/sh
/ $ find /galaxy/
/galaxy/
/galaxy/histories
/galaxy/histories/f597429621d6eb2b
/galaxy/histories/f597429621d6eb2b/f2db41e1fa331b3e
/galaxy/histories/f597429621d6eb2b/f597429621d6eb2b
/galaxy/histories/f597429621d6eb2b/1cd8e2f6b131e891
/galaxy/histories/f597429621d6eb2b/ebfb8f50c6abde6d
/galaxy/histories/f597429621d6eb2b/f2db41e1fa331b3e_dc
/galaxy/histories/f597429621d6eb2b/f2db41e1fa331b3e_dc/33b43b4e7093c91f
/galaxy/histories/f597429621d6eb2b/f2db41e1fa331b3e_dc/a799d38679e985db
/galaxy/histories/f597429621d6eb2b/f2db41e1fa331b3e_dc/5969b1f7201f12ae
/galaxy/histories/f597429621d6eb2b/f2db41e1fa331b3e_dc/df7a1f0c02a5b08e
/galaxy/histories/f597429621d6eb2b/f597429621d6eb2b_dc
/galaxy/histories/f597429621d6eb2b/f597429621d6eb2b_dc/33b43b4e7093c91f_dc
/galaxy/histories/f597429621d6eb2b/f597429621d6eb2b_dc/33b43b4e7093c91f_dc/ebfb8f50c6abde6d
/galaxy/histories/f597429621d6eb2b/f597429621d6eb2b_dc/33b43b4e7093c91f_dc/1cd8e2f6b131e891
/galaxy/histories/f597429621d6eb2b/f597429621d6eb2b_dc/df7a1f0c02a5b08e_dc
/galaxy/histories/f597429621d6eb2b/f597429621d6eb2b_dc/df7a1f0c02a5b08e_dc/f597429621d6eb2b
/galaxy/histories/f597429621d6eb2b/f597429621d6eb2b_dc/df7a1f0c02a5b08e_dc/f2db41e1fa331b3e

$ docker run -it --user 1000:1000 --mount type=volume,destination=/galaxy,volume-driver=galaxy,volume-opt=url=http://localhost,volume-opt=apikey=76d1a621e9d80751c1475c176ae6ee12,volume-opt=human_readable=true python:3.6-alpine /bin/sh
/ $ find /galaxy/
/galaxy/
/galaxy/histories
/galaxy/histories/Test __f597429621d6eb2b
/galaxy/histories/Test __f597429621d6eb2b/Pasted Entry __f2db41e1fa331b3e
/galaxy/histories/Test __f597429621d6eb2b/Pasted Entry __f597429621d6eb2b
/galaxy/histories/Test __f597429621d6eb2b/Pasted Entry __1cd8e2f6b131e891
/galaxy/histories/Test __f597429621d6eb2b/Pasted Entry __ebfb8f50c6abde6d
/galaxy/histories/Test __f597429621d6eb2b/list __f2db41e1fa331b3e_dc
/galaxy/histories/Test __f597429621d6eb2b/list __f2db41e1fa331b3e_dc/Pasted Entry __33b43b4e7093c91f
/galaxy/histories/Test __f597429621d6eb2b/list __f2db41e1fa331b3e_dc/Pasted Entry __a799d38679e985db
/galaxy/histories/Test __f597429621d6eb2b/list __f2db41e1fa331b3e_dc/Pasted Entry __5969b1f7201f12ae
/galaxy/histories/Test __f597429621d6eb2b/list __f2db41e1fa331b3e_dc/Pasted Entry __df7a1f0c02a5b08e
/galaxy/histories/Test __f597429621d6eb2b/list:paired __f597429621d6eb2b_dc
/galaxy/histories/Test __f597429621d6eb2b/list:paired __f597429621d6eb2b_dc/1 __33b43b4e7093c91f_dc
/galaxy/histories/Test __f597429621d6eb2b/list:paired __f597429621d6eb2b_dc/1 __33b43b4e7093c91f_dc/Pasted Entry __ebfb8f50c6abde6d
/galaxy/histories/Test __f597429621d6eb2b/list:paired __f597429621d6eb2b_dc/1 __33b43b4e7093c91f_dc/Pasted Entry __1cd8e2f6b131e891
/galaxy/histories/Test __f597429621d6eb2b/list:paired __f597429621d6eb2b_dc/2 __df7a1f0c02a5b08e_dc
/galaxy/histories/Test __f597429621d6eb2b/list:paired __f597429621d6eb2b_dc/2 __df7a1f0c02a5b08e_dc/Pasted Entry __f597429621d6eb2b
/galaxy/histories/Test __f597429621d6eb2b/list:paired __f597429621d6eb2b_dc/2 __df7a1f0c02a5b08e_dc/Pasted Entry __f2db41e1fa331b3e
```
