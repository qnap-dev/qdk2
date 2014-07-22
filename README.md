QDK2
===============

local build

```
$ debuild -us -uc
```

build source package

```
$ make -f Makefile.debian 
```

upload to PPA

```
dput ppa:fcwu-tw/ppa debuild/qdk2_0.5ubuntu1\~trusty_source.changes
dput ppa:fcwu-tw/ppa debuild/qdk2_0.5ubuntu1\~precise_source.changes
```
