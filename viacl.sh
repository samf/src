#! /bin/sh -e

# for use in Solaris

file="."
test -n "$1" && file="$1"

trap "rm -f /tmp/viacl.$$" 0

ls -ldV $file > /tmp/viacl.$$
${EDITOR:-vi} /tmp/viacl.$$
acl=`grep ':.*:.*:' /tmp/viacl.$$ | sed -e :a -e '$!N; s/\n/,/; s/ //g; ta`

chmod "A=$acl" $file
