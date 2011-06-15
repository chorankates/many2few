#!/usr/bin/perl -w
## many2few.cgi - main application

use strict;
use warnings;

use CGI ':standard';
#use CGI;
use DBI;
use Digest::MD5;
use File::Basename;
use File::Copy;
use Fcntl qw/:DEFAULT :flock/; # for uploading files
use IO::Handle;

## initalize some variables
my %s = (
    host => '192.168.1.122', # hardcoded for now
    
    # uploaded file settings
    dest_dir      => '/home/conor/scratch/many2few/', # for now, will copy to DB later
    buffer_size   => 16_384,
    max_file_size => 1_048_576 * 10, # limiting to 10mb 
    max_dir_size  => 1_048_576 * 1_000, # limiting to 1gb
    
    #dropbox => '/tmp/many2few/',
    #upload_log => '/tmp/many2few/upload.log',
    dropbox => '/home/conor/Dropbox/scratch/many2few/', # final resting place
    upload_log =>'/home/conor/scratch/many2few-upload.log',

    # need to externalize all settings, eventually
    regex => {
	wanted => [
	    '\.doc$',
	    '\.txt$',
	    '\.pl$',
	],
	unwanted => [ 
	    '\.zip$',
	    '\.exe$',
	    '.*', # wanted will override unwanted, so do we really need an unwanted list?
	],
    },

);

$CGI::DISABLE_UPLOADS = 0;
$CGI::POST_MAX        = $s{max_file_size};

print(
        header(),
        start_html(
            	-title=> "many2few - collaborate",
            	-text   => "black",
		-style => { src => '../style.css' }
        ),
        "<div class='header'>",
        "<h2><a href='/cgi-bin/many2few.cgi'>many2few</a> - one way file sharing</h2>",
        "</div>",
        "<div class='main'>",
    );


## traffic cop
unless (param()) {
    # display the main page
   
    print(
        "<form action='/cgi-bin/many2few.cgi' METHOD='POST' ENCTYPE='multipart/form-data'>",
        "<table>\n",
        "<input name='function' value='upload' type='hidden'\n>",
	"<input name='filename' value='tmp_file' type='hidden'\n>",
        "<tr><td>your name:</td><td><input name='user'>\n",
        "<tr><td>description:</td><td><input name='description'>\n",
	#"<tr><td>file to upload:</td><td><input type=file size=75 name='file'></tr>\n",
	# don't know that below is functionally different than above, need to test
	"<tr><td>file to upload:</td><td>", CGI::filefield('file', '', 50, 80), "</td></tr>\n",
        "<tr><td>&nbsp;</td><td><input type='submit'></td>\n",
        "</table>",
        "</form>",
    );
    
} else {
    # file being uploaded
	my $q = new CGI;
	my @parameters = param();
	my %p;
	#$p{$_} = param($_) foreach (@parameters);
	$p{function} = $q->param('function');
	$p{file} = param('file');

	print "<h2>unknown function</h2>" unless $p{function} eq 'upload';

    # security until it can be hardened
    #print "we received:\n";
    #print "<table><tr><td><strong>key<strong><td><td><strong>value<strong></td></tr>\n";
    #print "<tr><td>$_</td><td>$p{$_}</td></tr>\n" foreach (keys %p);
    #print "</table>";
	$s{outfile} = $p{file};
    
    #my ($results,$message) = write_file($s{dest_dir}, $p{file});
	my ($results,$message) = write_file($s{dest_dir}, $q);
    
    if ($results == 0) {
        my $md5 = get_md5($message) if $results == 0; # $message = filename if successful
        print "<br><h2>successful upload of file (MD5: $md5)</h2>" if $results == 0;
        print "<br><h2>error</h2>" if $results != 0;

        # now need to push it onto the CSV file -- maintain the schema by not pushing the entire ref blindly
        write_csv($p{member}, $md5, $s{outfile});
        
        #copy($message, $s{dropbox} . $s{outfile}) or warn "WARN:: unable to copy file to $s{dropbox}: $!";
	print "> message: $message\n<br>";
        #unlink($message);
		
    } else {
    
        print "<h2>unable to upload file: $message (error code: $results)</h2>";
    }

}

if (0) {
    print(
        "</div>", # closing main div
        "<div class='footer'>",
        "some text goes here",
        "</div>",
    );
}

## cleanup

exit;

## functions below

sub write_file {
    # write_file($dir, $filename) - writes CGI received data to disk.. danger will robinson, danger. returns (0,filename) for success, (1,error message) otherwise
    my ($dir, $q) = @_;
    my $results = 0;
    
    use constant BUFFER_SIZE      => $s{buffer_size};
    use constant MAX_FILE_SIZE    => $s{max_file_size};
    use constant MAX_DIR_SIZE     => $s{max_dir_size};
    use constant MAX_OPEN_RETRIES => 100;
 
    #use Data::Dumper;
    #print Dump($q);

    return (1, $q->cgi_error) if $q->cgi_error;
    return (1, "unsupported file type") unless is_wanted($q->param('file'));

    my $file         = $q->param("file") or warn "WARN:: unable to use file '", $q->param("file"), "' as a parm: $!";
    #my $fh           = $q->upload( $file );
    my $fh           = $file;

	
    #my $filename_out = $q->param("filename");
    my $filename_out = $s{outfile};
       $filename_out =~ s/[^\w.-\\\/\?;\*]/_/g; # weak   
    my $buffer = "";
    my $ffp = $dir . $filename_out;
    
    #print(
    #"file: ", $file, "\n<br>",
    #"fh: ", $fh, "\n<br>",
    #"out: $filename_out\n<br>",
    #"ffp: $ffp\n<br>",
    #"tmp: ", $q->tmpFileName($file), "\n",
    #"error: ", $q->cgi_error, "end of error\n",
    #);
	
    if (defined $fh) {
	my $io_handle = $fh->handle;
	my $bytesread;
	
	open (OUTFILE,'>>',$ffp) or warn "WARN:: unable to open '$ffp': $!\n";
	while ($bytesread = $io_handle->read($buffer,1024)) {
	    print OUTFILE $buffer;
	}
    } else {
		
    }
    
    return (0, $ffp);
}


sub get_select {
    # get_select($name) - returns an HTML string composed of a complete select control
    my $name = shift;
    my $html;
    
    my @elements;
    if ($name eq 'member') {
	# populate @elements here
    } elsif ($name eq 'something') { 
	# and here
    }

    $html = "<select name='$name'>";
    $html .= "<option value='$_'>$_</option>" foreach (@elements);
    $html .= "</select>";
    
    return $html;
}

sub write_csv {
    # write_csv($user, $description, $md5, $filename) - quick and dirty logging.. this should really be in SQLite.. returns 0|1 for success|failure
    my ($member, $md5, $filename) = @_;
    my $results = 0;
    
    my $string = join(',', ($member, $md5, $filename)); # just in case we want to do some processing later
	
    open(my $fh, '>>', $s{upload_log}) or warn "WARN:: unable to log this upload to '$s{upload_log}': $!";
    print $fh $string . "\n"	;
    close ($fh);
    
    return $results;
}

# could move this to a library for testing
sub is_wanted {
    # is_wanted($filename) - returns 0|1 on whether we want the file they are trying to upload
    my $file    = shift;

    foreach my $wanted (@{$s{regex}{wanted}}) {
	return 1 if $file =~ /$wanted/;
    }

    return 0; 
}

# could move this to a library for testing
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
