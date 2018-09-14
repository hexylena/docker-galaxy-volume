# GFS Docker Volume Plugin

## Installation

Create a 'galaxy' spec file in `/etc/docker/plugins/galaxy.spec` containing:

```
tcp://localhost:8123
```

## Running

```
make
```


## Usage

Create a volume

```
$ docker volume create --driver=galaxy -o apikey=<apikey> -o server=<url> test
test
```

Added a `status` api so you can check what is currently known to the system:

```
$ curl localhost:8123/status
{
  "test": {
    "apikey": "asdf",
    "url": "https://usegalaxy.eu",
    "name": "test"
  }
}
```


See that we've created a volume with our others:

```
$ docker volume ls
DRIVER              VOLUME NAME
local               f5fbbe35febaf4f9002860bce281a794e2766b37cc941f5bd8e42260e8290c35
...
galaxy              test
```

And we can inspect it:


```
$ docker volume inspect test
[
    {
        "CreatedAt": "0001-01-01T00:00:00Z",
        "Driver": "galaxy",
        "Labels": {},
        "Mountpoint": "",
        "Name": "test",
        "Options": {
            "apikey": "asdf"
            "url": "https://usegalaxy.eu"
        },
        "Scope": "global"
    }
]
```

So let's run a container with it:

```
$ docker run -it --user 1000 -v test:/galaxy:ro --entrypoint=/bin/sh python:3.6-alpine
/ $ ls /
bin     dev     etc     galaxy  home    lib     media   mnt     proc    root    run     sbin    srv     sys     tmp     usr     var
/ $ ls /galaxy/
histories
/ $ ls /galaxy/histories/
Unnamed history [aa4561359a9096a0]                                                   imported: Y3line2tissAnalysis-run1 [da3a6d229e422dde]
imported: 65991-A ASaiM - Shotgun workflow for paired-end data 2 [a8eb2fef93d4f4e1]
```

Nice!. Exiting the container we can look at it again and see that the mountpoint is now specified:

```
$ docker volume inspect test
[
    {
        "CreatedAt": "0001-01-01T00:00:00Z",
        "Driver": "galaxy",
        "Labels": {},
        "Mountpoint": "/tmp/93d34877c02042309637d545e89e5ad8",
        "Name": "test",
        "Options": {
            "apikey": "asdf"
            "url": "https://usegalaxy.eu"
        },
        "Scope": "global"
    }
]
```

And we'll cleanup (partially)

```
$ docker volume rm test
Error response from daemon: remove test: volume is in use - [355ab86cdec6d4b97eaa39029bdf234987e65323d8bec4c345d659860beaf750]
$ docker ps -a -q | xargs docker rm;
355ab86cdec6
$ docker volume rm test
test
```

Partial cleanup because this is just a hack and doesn't clean up the background processes it spawns:

```
$ ps aux | grep gfs
hxr      1963742  4.3  0.2  82568 24824 pts/10   S+   14:58   0:00 python gfs.py -m /tmp/273c7d396e454884b4c26185d1b77ec7 https://usegalaxy.eu <apikey>
```
