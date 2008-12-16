import Util.File

def localize_param_files(env, dirname=None): 
    """Make a temporary directory and put it at the head of env['PFILES'] so
    CIAO parameters for this session are localized there.

    Usage::
    >>> ciaoenv = Shell.getenv('. /soft/ciao/bin/ciao.bash')
    >>> pfiles_dir = Util.CIAO.localize_param_files(ciaoenv)
    
    @param env: (delta) environment mapping.  Must have PFILES.
    @param dirname: location of temporary directory (default=system tmp dir)
    @return: TempDir object.  The temp dir is deleted when TempDir object
             gets destroyed or goes out of scope.
    """
    try:
        pfiles = env['PFILES'].split(';')
    except KeyError:
        raise ValueError('PFILES key must be defined.')

    tempdir = Util.File.TempDir(dir=dirname)
    env['PFILES'] = ';'.join([tempdir.name] + pfiles)

    return tempdir
    
def dmmerge_files():
    """Placeholder for dmmerge routine.  Probably not needed, prefer to use .lis files"""
    raise ValueError('This routine is no implemented yet.')
## 	if (test_dep(-target => $out_files[0], -depend => \@files)) {
## 	    # Multiple files, need to merge them
## 	    my $list = join ',', @files;
## 	    my $ok = run_tool("dmmerge",
## 			      infile => $list,
## 			      columnList => '',
## 			      outfile => $out_files[0],
## 			      outBlock => '',
## 			      clobber => 'yes',
## 			      lookupTab => "$ENV{ASCDS_CALIB}/dmmerge_header_lookup.txt",
## 			      { timeout => $self->cfg->get_timeout,
## 				paste => 1,
## 				loud => 1,
## 			      }
## 			     );
## 	    return unless $ok;
## 	}
##     }
