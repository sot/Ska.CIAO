import tempfile
import re

import Ska.File
import Ska.Shell
import Ska.astro

def localize_param_files(env, dirname=None): 
    """Make a temporary directory and put it at the head of env['PFILES'] so
    CIAO parameters for this session are localized there.

    Usage::
    >>> ciaoenv = Shell.getenv('. /soft/ciao/bin/ciao.bash')
    >>> pfiles_dir = Util.CIAO.localize_param_files(ciaoenv)
    
    :param env: (delta) environment mapping.  Must have PFILES.
    :param dirname: location of temporary directory (default=system tmp dir)
    :returns: TempDir object.  The temp dir is deleted when TempDir object
             gets destroyed or goes out of scope.
    """
    try:
        pfiles = env['PFILES'].split(';')
    except KeyError:
        raise ValueError('PFILES key must be defined.')

    tempdir = Ska.File.TempDir(dir=dirname)
    env['PFILES'] = ';'.join([tempdir.name] + pfiles)

    return tempdir
    
def dmcoords(evtfile, asolfile, pos, coordsys, celfmt='deg', env=None):
    """Run dmcoords for coordinates ``pos`` which are in coordinate system ``coord``
    and return results as a dict.

    The ``pos`` parameter must be a list with values interpreted according to
    the ``coordsys`` parameter:

    =========  =====================
    coordsys   pos list values
    =========  =====================
    cel        ra, dec
    sky        x, y
    det        detx, dety
    logical    chip_id, chipx, chipy
    msc        theta, phi
    =========  =====================

    :param evtfile: x-ray event file
    :param asolfile: aspect solution file or list
    :param pos: list of coordinates
    :param coordsys: input coordinate system (cel|sky|det|logical|msc)
    :param celfmt: format for in/out RA and dec (deg|hms)
    :param env: CIAO environment dict (optional)

    :returns: dict corresponding to dmcoords parameter list and values
    """
    parmap = dict(cel=['ra', 'dec'],
                  sky=['x', 'y'],
                  det=['detx', 'dety'],
                  chip=['chip_id', 'chipx', 'chipy'],
                  logical=['logicalx', 'logicaly'],
                  msc=['theta', 'phi'])

    Ska.Shell.bash('punlearn dmcoords', env=env)

    if coordsys not in parmap:
        raise ValueError('coordsys=%s is not in allowed values %s'
                         % (coordsys, str(parmap.keys())))

    # Generate pset dmcoords par=val pairs for input pos and coordsys
    parsets = ['%s=%s' % (par, str(val)) for (par, val) in zip(parmap[coordsys], pos)]
    parsets.append('celfmt="%s"' % celfmt)
    cmd = 'pset dmcoords ' + ' '.join(parsets)
    Ska.Shell.bash(cmd, env=env)

    # Run dmcoords cmd to do conversion.  This should run silently, any output
    # indicates a problem.  Note also that dmcoords does not return non-zero
    # exit status on error like most tools (bug reported to ascds_help).
    cmd = 'dmcoords infile="%s" asolfile="%s" celfmt="%s" option="%s"' \
          % (evtfile, asolfile, celfmt, coordsys)
    out = Ska.Shell.bash(cmd, env=env)
    if out:
        raise ValueError('"%s" produced output:\n %s' % (cmd, '\n'.join(out)))

    # Values determined by dmcoords
    vals = dict()

    # Dump, parse and convert the parameter values in par='val' pairs
    for parval in Ska.Shell.bash('pdump dmcoords', env=env):
        match = re.match(r"(\w+)='(.+)'", parval)
        if match:
            par, val = match.groups()
            try:
                val = int(val)
            except ValueError:
                try:
                    val = float(val)
                except ValueError:
                    pass
            vals[par] = val

    return vals

def colden(ra, dec, env=None):
    """Determine Galactic column density at specified ``ra`` and ``dec``.
    This function calls the CIAO ``prop_colden_exe`` tool.

    :param ra: right ascension (J2000)
    :param dec: declination
    :param env: CIAO environment vars

    :returns: column density (10^22 cm^-2)
    """
    colden_in = tempfile.NamedTemporaryFile()  # Input to colden
    colden_out = tempfile.NamedTemporaryFile()  # Output from colden
    null = tempfile.NamedTemporaryFile()  # File to catch stdout from colden

    eq = Ska.astro.Equatorial(ra, dec)
    eq.delim = " "
    colden_in.write('%s %s\n' % (eq.ra_hms, eq.dec_dms))
    colden_in.flush()
    
    cmd = "prop_colden_exe d nrao f j2000 :%s:%s"  % (colden_in.name, colden_out.name)
    out = Ska.Shell.bash(cmd, logfile=null, env=env)

    gal_nh = None
    for line in colden_out:
	vals = line.split()
        if (len(vals) >= 9 and vals[8] != '-' and
            re.match(r'[-0-9.]+', vals[6]) and re.match(r'[-0-9.]+', vals[7])):
            gal_nh = float(vals[8]) / 100. # Convert from 10^20 (colden) to 10^22 (sherpa)
            break

    if gal_nh is not None:
        return gal_nh
    else:
        raise ValueError('Colden did not give valid NH')

