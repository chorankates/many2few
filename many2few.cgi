#!/usr/bin/perl -w
## many2few.cgi - main application

use strict;
use warnings;

use CGI ':standard';
use DBI;
use File::Basename;

## initalize some variables
my %s = (
    host => '192.168.1.122', # hardcoded for now
);

print(
        header(),
        start_html(
            	-title=> "many2few - collaborate",
            	-text   => "black",
		-style => { src => '../style.css' }
        ),
        "<div class='header'>",
        "<h2>many2few - one way file collaboration</h2>",
        "</div>",
        "<div class='main'>",
    );


## traffic cop
unless (param()) {
    # display the main page
   
    print(
        "<form action='/cgi-bin/many2few.cgi'>",
        "<table>",
        "<tr><td>your name:</td><td><input name='user'>",
        "<tr><td>description:</td><td><input name='description'>",
        "<tr><td>file to upload:</td><td><input type=file size=75 name='file'></tr>",
        "<tr><td>&nbsp;</td><td><input type='submit'></td>",
        "</table>",
        "</form>",
    );
    
} else {
    # file being uploaded
}

print(
    "</div>", # closing main div
    "<div class='footer'>",
    "some text goes here",
    "</div>",
);

## cleanup

exit;

## functions below