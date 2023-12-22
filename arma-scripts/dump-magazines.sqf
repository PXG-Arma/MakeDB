/*
 * Dumps magazine data to the system clipboard.
 *
 * Dump format:
 * <ID>;<display name>;<short name>;[<parents>...];
 * <description>;<ammo>;<count>
 */

_newLine = toString [0x0D, 0x0A];
_configs = "getNumber (_x >> 'scope') >= 1" configClasses (configFile >> "CfgMagazines") apply
{
 _newLine
 + configName(_x) + ";"
 + getText (_x >> "displayName") + ";"
 + getText (_x >> "displayNameShort") + ";"
 + str([_x, true] call BIS_fnc_returnParents) + ";"
 + getText (_x >> "descriptionShort") + ";"
 + getText (_x >> "ammo") + ";"
 + str(getNumber (_x >> "count"));
};
copyToClipBoard str _configs;
