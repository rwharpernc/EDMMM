"""
Classifies missions into the categories the panel scrolls through.

Elite Dangerous embeds mission type information in the internal `Name`
field as underscore-separated tags (e.g. "Mission_Massacre_Onslaught",
"Mission_Delivery_Illegal_MB"). This is undocumented by Frontier, but the
tag vocabulary is well established in the community (this mirrors the
EDDI project's MissionType.cs, the most complete public reference for it).
"""

MASSACRE_SPACE = "massacre_space"
MASSACRE_GROUND = "massacre_ground"
COMBAT = "combat"
TRADE = "trade"
PASSENGER = "passenger"
COVERT = "covert"
OTHER = "other"

CATEGORY_LABELS: dict[str, str] = {
    MASSACRE_SPACE: "Massacre (Space)",
    MASSACRE_GROUND: "Settlement Raids (Ground)",
    COMBAT: "Combat",
    TRADE: "Trade & Mining",
    PASSENGER: "Passenger",
    COVERT: "Covert / On-Foot Ops",
    OTHER: "Other",
}

CATEGORY_ORDER: list[str] = [
    MASSACRE_SPACE, MASSACRE_GROUND, COMBAT, TRADE, PASSENGER, COVERT, OTHER,
]

_MASSACRE_HINTS = ("massacre", "onslaught", "raid")
_COMBAT_HINTS = ("assassinate", "assassination", "disable", "skimmer", "conflict",
                 "blops", "piracy", "scout", "thargoid", "terminalprosecution",
                 "tacticaltakedown", "reclamationpoint", "biohazardtakedown",
                 "rapidresponse")
_TRADE_HINTS = ("delivery", "courier", "collect", "mining", "salvage",
                "colonisation", "communitygoal", "smuggle")
_PASSENGER_HINTS = ("passenger", "sightseeing", "vip", "bulk", "evacuation",
                    "polprisoner")
_COVERT_HINTS = ("hack", "covert", "heist", "sabotage", "reboot", "download",
                 "upload", "poi", "productionheist", "theft", "power",
                 "production", "ncd")
_ILLEGAL_HINTS = ("illegal", "smuggle")


def is_ground_mission(event: dict) -> bool:
    """
    On-foot missions have "OnFoot" in the internal name; settlement-targeted
    missions also carry a DestinationSettlement field.
    """
    return "onfoot" in event.get("Name", "").lower() \
        or bool(event.get("DestinationSettlement"))


def is_massacre_shaped(event: dict) -> bool:
    """
    Matches any mission whose objective is killing members of a faction:
    ship massacre missions (Mission_Massacre, Mission_MassacreWing, ...),
    on-foot massacre missions, and settlement raids (Mission_OnFoot_Onslaught*).

    Primary signal is the mission shape - a kill count against a target
    faction - so mission types with unexpected internal names still match.
    Name hints catch known variants that might omit one of the fields.
    """
    if event.get("KillCount") and event.get("TargetFaction"):
        return True
    name = event.get("Name", "").lower()
    return any(hint in name for hint in _MASSACRE_HINTS)


def is_illegal(event: dict) -> bool:
    name = event.get("Name", "").lower()
    return any(hint in name for hint in _ILLEGAL_HINTS)


def classify(event: dict) -> str:
    """Bucket a MissionAccepted event into one of the panel's category pages."""
    if is_massacre_shaped(event):
        return MASSACRE_GROUND if is_ground_mission(event) else MASSACRE_SPACE

    name = event.get("Name", "").lower()
    if any(hint in name for hint in _COMBAT_HINTS):
        return COMBAT
    if any(hint in name for hint in _TRADE_HINTS):
        return TRADE
    if any(hint in name for hint in _PASSENGER_HINTS):
        return PASSENGER
    if any(hint in name for hint in _COVERT_HINTS) or is_ground_mission(event):
        return COVERT
    return OTHER
