#!/usr/bin/perl -w
## many2few.cgi - main application

use strict;
use warnings;
use Fcntl qw/:DEFAULT :flock/; # for uploading files

use CGI ':standard';
use DBI;
use Digest::MD5;
use File::Basename;

## initalize some variables
my %s = (
    host => '192.168.1.122', # hardcoded for now
    
    # uploaded file settings
    dest_dir      => '/tmp/', # for now, will copy to DB later
    buffer_size   => 16_384,
    max_file_size => 1_048_576 * 10, # limiting to 10mb 
    max_dir_size  => 1_048_576 * 1_000, # limiting to 1gb
    
    dropbox => '/home/conor/scratch/many2few/', # final resting place
    upload_log =>'/home/conor/scratch/many2few/upload.log',
);

print(
        header(),
        start_html(
            	-title=> "many2few - collaborate",
            	-text   => "black",
		-style => { src => '../style.css' }
        ),
        "<div class='header'>",
        "<h2><a href='/cgi-bin/many2few.cgi'>many2few</a> - one way file collaboration</h2>",
        "</div>",
        "<div class='main'>",
    );


## traffic cop
unless (param()) {
    # display the main page
   
    print(
        "<form action='/cgi-bin/many2few.cgi' METHOD='POST' ENCTYPE='multipart/form-data'>",
        "<input name='function' value='upload' type='hidden'\n>",
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

    print "<h2>unknown function</h2>" unless $p{function} eq 'upload';

    print "we received:\n";
    print "<table><th><td>key<td><td>value</td></th>\n";
    print "<tr><td>$_</td><td>$p{$_}</td></tr>\n" foreach (keys %p);
    print "</table>";

    my ($results,$message) = write_file($s{dest_dir}, $p{file});
    
    if ($results == 0) {
        my $md5 = get_md5($message) if $results == 0; # $message = filename if successful
        print "<h2>successful upload of file (MD5: $md5)</h2>";
        
        # now need to push it onto the CSV file -- maintain the schema by not pushing the entire ref blindly
        write_csv($p{user}, $p{description}, $md5, $p{file});
        
        move($p{filename}, $s{dropbox});
        
    } else {
    
        print "<h2>unable to upload file: $message (error code: $results)</h2>";
    }

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

sub write_csv {
    # write_csv($user, $description, $md5, $filename) - quick and dirty logging.. this should really be in SQLite.. returns 0|1 for success|failure
    my ($user, $description, $md5, $filename) = @_;
    my $results = 0;
    
    my $string = join(',', ($user, $description, $md5, $filename)); # just in case we want to do some processing later
    
    open(my $fh, '>>', $s{upload_log}) or warn "WARN:: unable to log this upload to '$s{upload_log}': $!";
    print $fh $string;
    close ($fh);
    
    return $results;
}

sub write_file {
    # write_file($dir, $filename) - writes CGI received data to disk.. danger will robinson, danger. returns (0,filename) for success, (1,error message) otherwise
    my ($dir, $filename) = @_;
    my $results = 0;
    
    use constant BUFFER_SIZE      => $s{buffer_size};
    use constant MAX_FILE_SIZE    => $s{max_file_size};
    use constant MAX_DIR_SIZE     => $s{max_dir_size};
    use constant MAX_OPEN_RETRIES => 100;
 
    my $q = new CGI;

    return (1, $q->cgi_error) if $q->cgi_error;

    return "unsupported file type" unless is_wanted($filename);

    my $fh     = $filename;
    my $buffer = "";
    
    my $filename_out = $filename;
       $filename_out =~ s/[^\w.-\\\/\?;\*]/_/g; # weak
       
    my $ffp = $dir . $filename_out;
    
    until (sysopen OUTPUT, $ffp, O_CREAT | O_RDWR | O_EXCL) {
        $filename_out =~ s/(\d*)(\.\w+)$/($1||0) + 1 . $2/e;
        # $1 needs to be the count of loops here.. for now, forcing failure if we don't match the first time

        last unless -f $ffp;
        
        return (2, "error writing file to disk");
	
    }

    
    
    return (0, $ffp);
}

sub is_wanted {
    # is_wanted($filename) - returns 0|1 on whether we want the file they are trying to upload
    my $file = shift;
    my $results = 0;
    
    $results = 1; # hardcoding yes for now
    
    return $results;    
}

sub get_md5 {
    # get_md5($ffp) - returns an md5 or ? based on criteria
    my $ffp = shift;
    
    # if file DNE, return ?
    return '?' unless -f $ffp;
    
    # if file is larger than 2mb, return ?
    return '?' unless (stat($ffp))[7] < 1_048_576 * 2;
    
    # compute md5
    # eval block to prevent death
    open(FILE, $ffp) or return "?";
    my $md5;
    eval { 
        binmode(FILE);
        $md5 = Digest::MD5->new->addfile(*FILE)->hexdigest;
        close(FILE);
    };

    return "?" if $@;
    
    return uc($md5);
}