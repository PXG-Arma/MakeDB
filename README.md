# MakeDB

Tools to extract weapon, vehicle, etc. data from Arma 3, and package it into a neat JSON databases for further use.


## Directory Structure

| Directory        | Description                                 |
| ---------------- | ------------------------------------------- |
| `arma-scripts`   | SQF scripts to extract data from the Arma 3 |


## Usage

### Dumping Data from Arma 3

Vehicle and weapon data must be dumped from Arma 3 by using the SQF scripts in the `arma-scripts` directory. Follow the procedure below:

1. Run Arma 3 with the full PXG modpack.
1. Host a multiplayer game with any PXG template.
1. Open the SQF script for the type of data you want to dump, and copy its contents (without the leading comments at the top). For example, to dump vehicle data, copy the contents of `/arma-scripts/dump-vehicles.sqf` to the system clipboard.
1. When deployed as a player on the map, press ESC. Paste the script into the big window for code execution, and press `LOCAL EXEC` below it.
1. Open your favourite text editor, like Notepad++ or Vim (not word processor!), and paste the contents of the system clipboard in it. Save it as something like `vehicles.dat`.
1. If detailed turrets data is desired, repeat the procedure with the script `/arma-scripts/dump-weapons.sqf`, and save the data to `weapons.dat`.

### Making a Database of Vehicles

Once you've collected the data dumps from Arma, use the Python script, `makedb.py`, to process the data into a fairly usable JSON database.

If detailed turret data is not required, use only the vehicles data dump:
```shell
makedb.py -v vehicles.dat -o motorpool.json
```

To include the detailed turret data, make use of the weapons dump as well:
```shell
makedb.py -v vehicles.dat -w weapons.dat -o motorpool.json
```

Note that weapon data will only be applied to the turret IDs, that exist in the weapons dump. Non-existent IDs will be left as pure strings.

In both cases, the resulting file will be written to `motorpool.json` in the current working directory. It will overwrite anything previously there!

Magazine dump can be read by specifying the `-m` option, but is not used at the moment.

### Making a Database of Faction Motorpools

To make a database of faction motorpools, PXG templates are required. Get them from the [Templates repo](https://github.com/PXG-Arma/Templates). Then use the following command:

```shell
makedb.py -f 'Templates/PXG_Map/Scripts/Factions' -o factions.json
```

The path to the `Factions` directory can point to the `Scripts/Factions` subdirectory of any PXG map template.

Again, the program will overwrite anything with the path, specified after the `-o` flag.

### Help

To be introduced to the full range of command line options, run:
```shell
makedb.py -h
```

To make the script show additional information, use the `-d` flag. It's pretty nice.
