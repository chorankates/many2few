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
        "<form action='/cgi-bin/many2few.cgi' METHOD='POST' ENCTYPE='multipart/form-data'>",
	"<input name='function' type='hidden'\n>",
        "<table>\n",
        "<tr><td>your name:</td><td><input name='user'>\n",
        "<tr><td>description:</td><td><input name='description'>\n",
        "<tr><td>file to upload:</td><td><input type=file size=75 name='file'></tr>\n",
        "<tr><td>&nbsp;</td><td><input type='submit'></td>\n",
        "</table>",
        "</form>",
    );
    
} else {
    # file being uploaded
    my @parameters = param();
    my %p;
    $p{$_} = param($_) foreach (@parameters);

    print "we received:\n";
    print "<table><th><td>key<td><td>value</td></th>\n";
    print "<tr><td>$_</td><td>$p{$_}</td></tr>\n" foreach (keys %p);
    print "</table>";

    my $md5 = '';
    

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
