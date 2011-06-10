#!/bin/bash

run_dir=/home/conor/git/many2few/

cgi=many2few.cgi

echo "> -C check..."
perl -c $cgi
if [ $? != 0 ];
then
    echo "  $cgi failed -C check, bailing out"
    exit 1
fi

echo "> deploying.."
# copy the wrapper into apache
sudo cp -v $cgi /usr/local/apache2/cgi-bin/
sudo cp -v style.css /usr/local/apache2/htdocs/
sudo chmod -v +x /usr/local/apache2/cgi-bin/many2few.cgi
