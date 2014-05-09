#!/bin/sh

# Stop the service before we begin the removal.
if [ -x /etc/init.d/qdk ]; then
/etc/init.d/qdk stop
/bin/sleep 5
/bin/sync
fi

# Package specific routines as defined in package_routines.


# Remove QPKG directory, init-scripts, and icons.
/bin/rm -fr "/share/CACHEDEV1_DATA/.qpkg/QDK"
/bin/rm -f "/etc/init.d/qdk"
/usr/bin/find /etc/rcS.d -type l -name 'QS*QDK' | /usr/bin/xargs /bin/rm -f 
/usr/bin/find /etc/rcK.d -type l -name 'QK*QDK' | /usr/bin/xargs /bin/rm -f
/bin/rm -f "/home/httpd/RSS/images/QDK.gif"
/bin/rm -f "/home/httpd/RSS/images/QDK_80.gif"
/bin/rm -f "/home/httpd/RSS/images/QDK_gray.gif"

# Package specific routines as defined in package_routines.
{
	/bin/rm -f /etc/config/qdk.conf
}

# Package specific routines as defined in package_routines.


