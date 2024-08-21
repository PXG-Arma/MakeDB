#! /usr/bin/env python

import argparse
import json
import os
import sys

from pprint import pprint

#
# Constants
#

SCRIPT_NAME    = 'makedb.py'
SCRIPT_VERSION = '1.0.0'
SCRIPT_DATE    = '2024-08-21'

# Strings, that appear in magazine IDs. Used to differentiate weapon IDs
# from magazine IDs.
WEAPONS_EXCLUDE_LIST = ['_mag_', '_Mag', 'Rnd_', 'Laser', 'Magazine',
                       '_magazine', 'mining', 'Smoke', 'missiles',
                       'MASTERSAFE', 'fcsmag', 'Horn', 'rnds', '_YELLOW',
                       '_RED', '_GREEN', '_HEAT', '_SABOT', '_HE',
                       '_2Rnd', 'lasermag', 'mastersafe', '_2rnd',
                       '0rnd', 'MLRS_X',
                       'LOP_BM8', 'LOP_OF', 'LOP_BK', 'LOP_BR', 'LOP_UOF']

AVAIL_FACTIONS_BASE = 'PXG_Available_Factions_'
AVAIL_FACTIONS_BLUFOR = AVAIL_FACTIONS_BASE + 'Blue.sqf'
AVAIL_FACTIONS_OPFOR  = AVAIL_FACTIONS_BASE + 'Opfor.sqf'
AVAIL_FACTIONS_INDEP  = AVAIL_FACTIONS_BASE + 'Indep.sqf'

VARIANT_LIST_NAME = 'variantlist.sqf'
VARIANT_VEHICLES_PREFIX  = 'vehicles_'
VARIANT_VEHICLES_POSTFIX = '.sqf'

#
# Classes
#

class Vehicle:
    """Container for all relevant vehicle data."""
    id         = ''
    type       = ''
    name       = ''
    cargo      = 0
    crew       = 0
    passengers = 0

    def __init__(self):
        """Initialises each object with its own copy of arrays."""
        self.turrets = []

class Weapon:
    """Container for all relevant weapon data."""
    id          = ''
    name        = ''
    description = ''

class Magazine:
    """Container for all relevant magazine data."""
    id          = ''
    name        = ''
    short_name  = ''
    description = ''

class Factions:
    """The root container for all factions."""
    def __init__(self):
        """Initialises each object with its own copy of arrays."""
        self.blufor = []
        self.opfor  = []
        self.indep  = []

class Faction:
    """Container for faction data."""
    name = ''

    def __init__(self):
        """Initialises each object with its own copy of arrays."""
        self.variants = []

class FactionVariant:
    """Container for data of a particular faction variant."""
    name = ''
    era  = ''
    
    def __init__(self):
        """Initialises each object with its own copy of arrays."""
        self.motorpool = []

class FactionMpoolGroup:
    """Container for a motorpool group of vehicles."""
    group = ''
    
    def __init__(self):
        """Initialises each object with its own copy of arrays."""
        self.vehicles = []

class FactionMpoolVehicle:
    """Container for a motorpool vehicle data inside a group."""
    id    = ''
    cargo = ''

#
# Globals
#

enable_debug = False

vehicles = []
weapons  = {}
mags     = {}
factions = Factions()

#
# Functions
#

# General utility

def eprint(*args, **kwargs):
    """Prints to STDERR."""
    print(*args, file=sys.stderr, **kwargs)

def debug_print(*args, **kwargs):
    """Prints to STDERR, if debug output is enabled."""
    global enable_debug
    if enable_debug:
        eprint(*args, **kwargs)

# Command line args

def parse_args():
    """Parses command line arguments and returns the resulting parser object.
    """
    p = argparse.ArgumentParser(
            prog=SCRIPT_NAME,
            description='Arma 3 motorpool database generator'
            )
    p.add_argument('-v', '--vehicles',
                   help='vehicles dump file',
                   metavar='VEHICLES_FILE',
                   dest='vehicles_file'
                   )
    p.add_argument('-w', '--weapons',
                   help='weapons dump file',
                   metavar='WEAPONS_FILE',
                   dest='weapons_file'
                   )
    p.add_argument('-m', '--mags',
                   help='magazines dump file',
                   metavar='MAGS_FILE',
                   dest='mags_file'
                   )
    p.add_argument('-f', '--factions',
                   help='factions template directory',
                   metavar='FACTIONS_DIR',
                   dest='factions_dir'
                   )
    p.add_argument('-o', '--output',
                   help='output JSON file (otherwise writing to STDOUT)',
                   metavar='OUT_FILE',
                   dest='out_file',
                   required=True
                   )
    p.add_argument('-d', '--debug',
                   help='turn on debug output',
                   dest='debug',
                   action='store_true'
                   )
    return p.parse_args()

# Arma 3 data dump parsing

def process_vehicles_line(line):
    """Processes the vehicle dump line and returns the Vehicle object.
    In case of errors, None is returned.
    """
    v = Vehicle()

    spl = line.split(';')
    if len(spl) < 10:
        return None

    v.id         = spl[0]
    v.type       = spl[1]
    v.name       = spl[2]
    v.cargo      = spl[5]
    v.crew       = spl[6]
    v.passengers = spl[7]

    # Parse turrets
    turrets = spl[8]
    turrets = turrets.lstrip('[').rstrip(']')
    turrets = turrets.split(',')
    cnt = 0
    inside = False
    for w in turrets:
        if len(w) == 0:
            continue

        cnt += 1
        if not inside:
            if 1 == cnt:
                # Turret name on the vehicle
                pass
            elif 2 == cnt:
                # Unknown number 0|1
                pass
            elif 3 == cnt:
                # Turret components and mags
                if w.startswith('['):
                    inside = True
                    w = w.lstrip('[')
            else:
                return None

        if inside:
            if w.endswith(']'):
                w = w.rstrip(']')
                inside = False
                cnt = 0

            w = w.lstrip('""').rstrip('""')
            # Filter out things, that aren't weapons
            if len(w) > 0:
                exclude = False
                for excl in WEAPONS_EXCLUDE_LIST:
                    if w.find(excl) >= 0:
                        exclude = True
                        break
                if not exclude:
                    v.turrets.append(w)

    return v

def process_weapons_line(line):
    """Processes the weapons dump line and returns the Weapon object.
    In case of errors, None is returned.
    """
    w = Weapon()

    spl = line.split(';')
    if len(spl) < 6:
        return None

    w.id          = spl[0]
    w.name        = spl[1]
    w.description = spl[2]

    return w

def process_mags_line(line):
    """Processes the mags dump line and returns the Magazine object.
    In case of errors, None is returned.
    """
    m = Magazine()

    spl = line.split(';')
    if len(spl) < 7:
        return None

    m.id          = spl[0]
    m.name        = spl[1]
    m.short_name  = spl[2]
    m.description = spl[4]

    return m

def read_vehicles_dump_file(path):
    """Reads vehicles dump file at the specified path, and saves the data to
    a global variable.
    Exits the script in the case of errors.
    """
    global vehicles

    debug_print(f":: Reading vehicles dump file '{args.vehicles_file}'")
    with open(path, 'r') as file:
        for line in file:
            if (len(line) < 10):
                continue
            v = process_vehicles_line(line)

            if v is None:
                eprint(f"Could not parse vehicle line '{line}'")
                sys.exit(1)
            else:
                vehicles.append(v)

    c = len(vehicles)
    debug_print(f"=> Read {c} vehicle entries")

def read_weapons_dump_file(path):
    """Reads weapons dump file at the specified path, and saves the data to
    a global variable.
    Exits the script in the case of errors.
    """
    global weapons

    debug_print(f":: Reading weapons dump file '{args.weapons_file}'")
    with open(path, 'r') as file:
        for line in file:
            if (len(line) < 10):
                continue
            w = process_weapons_line(line)

            if w is None:
                eprint(f"Could not parse weapon line '{line}'")
                sys.exit(1)
            else:
                weapons[w.id] = w

    c = len(weapons)
    debug_print(f"=> Read {c} weapon entries")

def read_mags_dump_file(path):
    """Reads mags dump file at the specified path, and saves the data to
    a global variable.
    Exits the script in the case of errors.
    """
    global mags

    debug_print(f":: Reading mags dump file '{args.mags_file}'")
    with open(path, 'r') as file:
        for line in file:
            if (len(line) < 10):
                continue
            m = process_mags_line(line)

            if m is None:
                eprint(f"Could not parse mag line '{line}'")
                sys.exit(1)
            else:
                mags[m.id] = m

    c = len(mags)
    debug_print(f"=> Read {c} magazine entries")

# Additional motorpool generation utilities

def enhance_turret_data():
    """If available, uses data from the weapons dump to enhance the data about
    the turrets in the vehicles database.
    Does nothing if weapon data is not available.
    Complains about unknown turret IDs.
    """
    global vehicles
    global weapons

    if len(weapons) > 0:
        debug_print(':: Weapon data is available - replacing turret IDs ' +
                    'with weapon data')
        not_found = []

        for v in vehicles:
            for i, t in enumerate(v.turrets):
                if t in weapons:
                    v.turrets[i] = weapons[t]
                else:
                    if t not in not_found:
                        not_found.append(t)
                        eprint(f"-- Unknown turret ID: '{t}'")

# JSON

def write_json_file(data_obj, path):
    """Serializes `data_obj` to JSON, and writes the result to the file with
    the given path.
    """
    with open(path, 'w') as file:
        json.dump(
                data_obj,
                fp=file,
                default=vars,
                indent=4
                )

# Faction parsing

def parse_factions(factions_dir):
    """Parses faction data from the `Scripts/Factions` folder of PXG templates.
    Exits the script in the case of errors.
    """
    global factions

    blf = read_available_factions(
            os.path.join(factions_dir, AVAIL_FACTIONS_BLUFOR))
    opf = read_available_factions(
            os.path.join(factions_dir, AVAIL_FACTIONS_OPFOR))
    ind = read_available_factions(
            os.path.join(factions_dir, AVAIL_FACTIONS_INDEP))

    debug_print(f"=> Found {len(blf)} BLUFOR, {len(opf)} OPFOR, " +
                f"and {len(ind)} INDEP factions.")

    debug_print('\n=> BLUFOR')
    parse_faction_dir_list(factions.blufor, factions_dir, *blf)
    debug_print('\n=> OPFOR')
    parse_faction_dir_list(factions.opfor,  factions_dir, *opf)
    debug_print('\n=> INDEP')
    parse_faction_dir_list(factions.indep,  factions_dir, *ind)
    debug_print()

def read_available_factions(path):
    """Reads an available factions file, and returns an array of factions,
    found in the file.
    """
    factions = []

    with open(path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line.startswith('"'):
                continue

            # Strip the leading '"' and the trailing '",'
            f = line.strip('",')
            factions.append(f)

    return factions

def read_variant_list(path):
    """Reads a faction variant list file, and returns an array of
    available variants, found in the file.
    Exits the script on errors.
    """
    variants = []

    with open(path, 'r') as file:
        start_found = False
        end_found = False

        vlist = ''

        # Capture everything between '[' and ']' across multiple lines
        for line in file:
            line = line.strip()
            # Skip empty and comment lines
            if line == '' or line.startswith('//'):
                continue

            ob = line.find('[')
            cb = line.rfind(']')

            if not start_found:
                if ob >= 0:
                    start_found = True
                    line = line[ob+1:]
            else:
                if cb >= 0:
                    end_found = True
                    line = line[:cb]

            vlist += line;
            if end_found:
                break

        if not end_found:
            eprint(f"Error reading variant list file '{path}': "
                   "no closing bracket found.")
            sys.exit(1)

        # Parse variant names from the list
        words = vlist.split(',')
        for w in words:
            w = w.strip()
            if w == '':
                continue
            if w.startswith('"') and w.endswith('"'):
                w = w.strip('"')
                # Skip separator entries
                if not w.startswith('-'):
                    variants.append(w)
            else:
                eprint(f"Error reading variant list file '{path}': "
                       f"could not parse word '{w}'")
                sys.exit(1)

    return variants

def read_variant_motorpool(path, dest_array):
    """Reads a motorpool file of a faction variant, and appends the
    motorpool vehicle groups to `dest_array`.
    Exits the script on errors.
    """
    stage = 1
    json_data = ''

    with open(path, 'r') as file:
        for line in file:
            # Start reading where the array begins
            if stage == 1:
                if line.strip().startswith('['):
                    stage += 1
                    json_data += line
            elif stage == 2:
                if line.strip().endswith('];'):
                    stage += 1
                    json_data += ']'
                else:
                    # Remove potential comments
                    i = line.rfind('//')
                    if i >= 0:
                        line = line[:i]
                    json_data += line
            # Stop reading after the array ends
            elif stage == 3:
                break

    # Replace invalid quotes
    json_data = json_data.replace("'", '"')

    # Try to parse as JSON
    try:
        data = json.loads(json_data)
    except Exception as e:
        eprint(f"Failed to read motorpool file '{path}' as JSON:")
        eprint(e)
        sys.exit(1)

    # Process all the vehicle groups
    group_count = 0
    vehicle_count = 0
    for group in data:
        if len(group) != 2:
            eprint(f"Error reading groups in motorpool file '{path}'.")
            sys.exit(1)

        g = FactionMpoolGroup()
        g.group = group[0]

        vehicles = group[1]
        for vehicle in vehicles:
            if len(vehicle) != 2:
                eprint("Error reading vehicle data in motorpool file " +
                       f"'{path}': vehicle entry does not consist of two fields.")
                eprint('Dump of the vehicle entry:')
                pprint(vehicle)
                sys.exit(1)

            v = FactionMpoolVehicle()
            v.id    = vehicle[0]
            v.cargo = int(vehicle[1])

            g.vehicles.append(v)
            vehicle_count += 1

        dest_array.append(g)
        group_count += 1

    debug_print(f" ({group_count} g, {vehicle_count} v)")

def parse_faction_dir(faction_dir, faction_name):
    """Parses data from a faction directory, and returns a `Faction` object.
    Returns `None` in case of errors.
    """
    f = Faction()
    f.name = faction_name

    variants = read_variant_list(
            os.path.join(faction_dir, VARIANT_LIST_NAME))
    if len(variants) == 0:
        eprint(f"Zero variants for faction '{faction_name}'.")
        return None

    if len(variants) > 1:
        debug_print(f"   {faction_name}:")

    for v in variants:
        words = v.split()
        if len(words) != 2:
            eprint(f"Invalid number of words in variant '{v}'.")
            return None

        fv = FactionVariant()
        fv.name = words[0]
        fv.era  = words[1]

        # Figure out whether the vehicle motorpool name is upper- or lower-cased
        fv_names = [fv.name, fv.name.lower()]
        
        # Generate additional possible file name with lowercase variant name and
        # uppercase camo
        i = fv.name.find('(')
        if i > 0:
            p1 = fv.name[:i]
            p2 = fv.name[i:]
            fv_names.append(p1.lower() + p2)

        vehicles_file_found = False
        for name in fv_names:
            mpname = VARIANT_VEHICLES_PREFIX + name + \
                    VARIANT_VEHICLES_POSTFIX
            mppath = os.path.join(faction_dir, fv.era, mpname)
            if os.path.isfile(mppath):
                vehicles_file_found = True
                break
        if not vehicles_file_found:
            eprint(f"Could not find motorpool file '{mppath}'.")
            sys.exit(1)

        if len(variants) > 1:
            debug_print(f"      * {fv.name} {fv.era}", end='')
        else:
            debug_print(f"   {faction_name}: {fv.name} {fv.era}", end='')
        read_variant_motorpool(mppath, fv.motorpool)

        f.variants.append(fv)

    return f

def parse_faction_dir_list(dest_array, base_dir, *faction_dirs):
    """Parses a list of faction directories, and appends the results to
    the given array
    Exits the script on errors.
    """
    for fd in faction_dirs:
        fp = os.path.join(base_dir, fd)
        f  = parse_faction_dir(fp, fd)

        if f is None:
            eprint(f"Failed to read faction data from '{fp}'.")
            sys.exit(1)
        else:
            dest_array.append(f)

#
# MAIN
#

if __name__ == '__main__':
    #
    # Parse command line args
    #

    args = parse_args()
    if args.debug:
        enable_debug = True

    debug_print(f"{SCRIPT_NAME} {SCRIPT_VERSION} ({SCRIPT_DATE})\n")

    #
    # Figure out what to do, and execute it
    #

    # -> Make faction database
    if args.factions_dir is not None:

        # Parse faction data from the factions directory
        debug_print(f":: Parsing factions from '{args.factions_dir}")
        parse_factions(args.factions_dir)

        # Write JSON file
        if len(factions.blufor) == 0 and \
           len(factions.opfor)  == 0 and \
           len(factions.indep)  == 0:
            eprint('No faction data')
            sys.exit(1)

        debug_print(f":: Writing faction database to file '{args.out_file}'")
        write_json_file(factions, args.out_file)

    # -> Make motorpool database
    elif args.vehicles_file is not None:

        # Read Arma 3 dump files
        read_vehicles_dump_file(args.vehicles_file)
        if args.weapons_file is not None:
            read_weapons_dump_file(args.weapons_file)
        if args.mags_file is not None:
            read_mags_dump_file(args.mags_file)

        # Prepare database
        enhance_turret_data()

        # Write JSON file
        if len(vehicles) == 0:
            eprint('No vehicle data')
            sys.exit(1)

        debug_print(f":: Writing motorpool database to file '{args.out_file}'")
        write_json_file(vehicles, args.out_file)

    # -> Incompetent user, do nothing
    else:
        eprint('Neither vehicles dump file, nor factions dir were specified.')
        sys.exit(1)

    debug_print(":: Done. Have a nice day.")
