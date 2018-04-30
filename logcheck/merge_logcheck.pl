#!/usr/bin/env perl

use strict;
use warnings;
use 5.010;

use File::Slurp qw(slurp);
use List::Util qw(uniq);

my @lines = slurp(\*STDIN);
@lines = grep { length and not m{ ^ \# }x } @lines;
@lines = uniq sort @lines;

my $section = '';
for my $line (@lines) {
	if ($line =~ m{^\Q^\w{3} [ :0-9]{11} \E\S+ (?<section>[0-9a-zA-Z-]+)}) {
		if ($section ne $+{section}) {
			$section = $+{section};
			say "\n# ${section}";
		}
	}
	print $line;
}
