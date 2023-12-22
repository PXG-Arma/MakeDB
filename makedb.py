#! /usr/bin/env python

import argparse
import json
import sys

#
# Constants
#

SCRIPT_NAME    = 'makedb.py'
SCRIPT_VERSION = '0.1.0'
SCRIPT_DATE    = '2023-12-22'

# String, that appear in magazine IDs. Used to differentiate weapon IDs
# from magazine IDs.
WEAPONS_EXLUDE_LIST = ['_mag_', '_Mag', 'Rnd_', 'Laser', 'Magazine',
                       '_magazine', 'mining', 'Smoke', 'missiles',
                       'MASTERSAFE', 'fcsmag', 'Horn', 'rnds', '_YELLOW',
                       '_RED', '_GREEN', '_HEAT', '_SABOT', '_HE',
                       '_2Rnd', 'lasermag', 'mastersafe', '_2rnd',
                       '0rnd', 'MLRS_X',
                       'LOP_BM8', 'LOP_OF', 'LOP_BK', 'LOP_BR', 'LOP_UOF']

#
# Globals
#

enable_debug = False

vehicles = []
weapons  = {}
mags     = {}

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

#
# Functions
#

def eprint(*args, **kwargs):
    """Prints to STDERR."""
    print(*args, file=sys.stderr, **kwargs)

def debug_print(*args, **kwargs):
    """Prints to STDERR, if debug output is enabled."""
    global enable_debug
    if enable_debug:
        eprint(*args, **kwargs)

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
                   dest='vehicles_file',
                   required=True
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
    p.add_argument('-o', '--output',
                   help='output JSON file (otherwise writing to STDOUT)',
                   metavar='OUT_FILE',
                   dest='out_file'
                   )
    p.add_argument('-d', '--debug',
                   help='turn on debug output',
                   dest='debug',
                   action='store_true'
                   )
    return p.parse_args()

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
                for excl in WEAPONS_EXLUDE_LIST:
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
    # Read vehicles dump file
    #

    debug_print(f":: Reading vehicles dump file '{args.vehicles_file}'")
    with open(args.vehicles_file, 'r') as file:
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

    #
    # Read weapons dump file
    #

    if args.weapons_file is not None:
        debug_print(f":: Reading weapons dump file '{args.weapons_file}'")

        with open(args.weapons_file, 'r') as file:
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

    #
    # Read mags dump file
    #

    if args.mags_file is not None:
        debug_print(f":: Reading mags dump file '{args.mags_file}'")

        with open(args.mags_file, 'r') as file:
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

    #
    # Prepare database
    #

    # Replace turret IDs with real weapon data
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


    #
    # Write JSON file
    #

    if len(vehicles) == 0:
        eprint('No vehicle data')
        sys.exit(1)

    # Write to STDOUT
    json_dest = sys.stdout
    file = None
    # Write to file
    if args.out_file is not None:
        debug_print(f":: Writing database to file '{args.out_file}'")
        file = open(args.out_file, 'w')
        json_dest = file
    else:
        debug_print(":: Writing database to STDOUT")

    json.dump(
            vehicles,
            fp=json_dest,
            default=vars,
            indent=4
            )

    if file is not None:
        file.close()

    debug_print(":: Done. Have a nice day.")
