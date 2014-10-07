QDK2
====

Build
-----

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

Commands
--------

**Create a new QPKG from the various source**

* import from contents of archive

```
qdk2 import --archive ./phpMyAdmin.tar.xz -p phpmyadmin
qdk2 import --archive http://ftp.gnu.org/gnu/wget/wget-1.15.tar.xz
qdk2 import --archive ftp://ftp.gnu.org/gnu/wget/wget-1.15.tar.xz
```

* import from existing folder

```
qdk2 import --folder /path/to/project/ -p myproject
```

* import from git/svn repository

```
qdk2 import --repository docker/docker -p docker
qdk2 import --repository https://github.com/bower/bower.git -p bower
qdk2 import --repository http://svn.redmine.org/redmine/trunk/ -p redmine
```

* import from Linux container (lxc/docker)

```
qdk2 import --container lxc u1 -p lxc_u1
qdk2 import --container docker 826544226fdc -p docker_ubuntu
```

* import from built-in samples (/usr/share/qdk2/samples/)

```
qdk2 import --sample dummy -p dummy_project
```

**Create a new QPKG from the template**

* create new empty project (only has qpkg config)

```
qdk2 create -p empty
```

* create new project from built-in template

```
qdk2 create --template c_cpp -p helloworld
```

**Build QPKG with QPKG_DIR**

```
cd $QPKG_DIR
qdk2 build
```

**Show QPKG information**
```
qdk2 info
```

**Tool for maintenance of the QNAP/changelog file in a source package**

```
qdk2 changelog
```

**Extract QNAP App (.qpkg) or firmware image (.img)**
    
* extract QNAP App package

```
qdk2 extract helloworld_1.0_all.qpkg
```

* extract QNAP firmware image

```
qdk2 extract SS-X53_20140822-4.1.1.img
```

**Check your system (development environment) for problems**

```
qdk2 doctor
```

**Show the QDK2 version information**

```
qdk2 version
```
