/*
 * Dumps weapon data to the system clipboard.
 *
 * Dump format:
 * <ID>;<display name>;<description>;[<parents>...];
 * [<item type>...];[<magazines>...]
 */

_newLine = toString [0x0D, 0x0A];

_configs = "getNumber (_x >> 'scope') >= 1" configClasses (configFile >> "CfgWeapons") apply
{
    _itemType = (configName _x) call BIS_fnc_itemType;

    _newLine
    + configName(_x) + ";"
    + getText (_x >> "displayName") + ";"
    + getText (_x >> "descriptionShort") + ";"
    + str([_x, true] call BIS_fnc_returnParents) + ";"
    + str _itemType + ";"
    + str(getArray (_x >> "magazines"));
};

copyToClipBoard str _configs;
