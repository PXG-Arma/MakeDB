/*
 * Dumps vehicle data to the system clipboard.
 *
 * Dump format:
 * <ID>;<singular name>;<display name>;[<parents>...];
 * <has cargo>;<cargo space>;<crew count>;<passenger count>;
 * [<turrets>...];[<weapons>...]
 */

_newLine = toString [0x0D, 0x0A];

_configs = "getNumber (_x >> 'scope') >= 0 &&
(configName _x isKindOf 'Car'
|| configName _x isKindOf 'Air'
|| configName _x isKindOf 'Tank'
|| configName _x isKindOf 'Ship'
|| configName _x isKindOf 'NATO_Box_Base'
|| configName _x isKindOf 'ContainerSupply'
|| configName _x isKindOf 'Bag_Base'
|| configName _x isKindof 'Slingload_base_F') " configClasses (configFile >> "CfgVehicles") apply
{
    _crewCount = [configName (_x),false] call BIS_fnc_crewCount;
    _passengerCount = [configName (_x),true] call BIS_fnc_crewCount;
    _passengerCount = _passengerCount - _crewCount;
    _turrets = [];
    _turretConfigs = configProperties[_x >> "Turrets"];
    {
        if (getText (_x >> "gun") != "") then
        {
            _turrets pushBack configName(_x);
            _turrets pushBack getNumber(_x >> "primaryGunner");
            _turrets pushBack ((getArray (_x >> "weapons")) + (getArray (_x >> "magazines")));
        };
    } forEach _turretConfigs;

    _newLine
    + configName(_x) + ";"
    + getText (_x >> "textSingular") + ";"
    + getText (_x >> "displayName") + ";"
    + str([_x, true] call BIS_fnc_returnParents) + ";"
    + str(getNumber (_x >> "ace_cargo_hasCargo")) + ";"
    + str(getNumber (_x >> "ace_cargo_space")) + ";"
    + str _crewCount + ";"
    + str _passengerCount + ";"
    + str _turrets + ";"
    + str(getArray (_x >> "weapons") + getArray (_x >> "magazines"));
};

copyToClipBoard str _configs;
