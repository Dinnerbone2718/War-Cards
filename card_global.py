import entity as e
from card import EntityCard, TankEntityCard, ArtilleryEntityCard, HelicopterEntityCard


updated_base_cords = [(99999,99999), (99999,99999)]


card_instances = {
    "small_tank": TankEntityCard(e.smallTank(1, 1, True), 20, scale=.8),
    "supply_truck": EntityCard(e.supplyTruck(1, 1, True), 10, scale=1),
    "small_plane": EntityCard(e.smallPlane(1, 1, True), 30, scale=.5),
    "infantry": EntityCard(e.infantry(1, 1, True), 2, scale=1),
    "artillery": ArtilleryEntityCard(e.artillery(1, 1, True), 20, scale=1, cannon_offset=(0, 0, 0.4)),
    "stealth_plane": EntityCard(e.stealthPlane(1, 1, True, updated_base_cords), 75, scale=.3),
    "sniper": EntityCard(e.sniper(1, 1, True), 5, scale=1),
    "anti_air": EntityCard(e.antiAir(1, 1, True), 30, scale=0.8),
    "helicopter": HelicopterEntityCard(e.tHelicopter(1, 1, True), 20, blades_offset = (0, -.28, .5), scale= .8),
    "attack_helicopter": HelicopterEntityCard(e.attHelicopter(1, 1, True), 75, blades_offset = (0, -.28, .5), scale= .8),
    "bomber": EntityCard(e.bomber(1, 1, True, updated_base_cords), 75, scale= .4),
    "battle_ship": EntityCard(e.battleship(1, 1, True), 90, scale= .4),
    "medium_tank": TankEntityCard(e.mediumTank(1, 1, True), 50, scale=.8),
    "atv": EntityCard(e.atv(1, 1, True), 20, scale= .5),

}

owned_cards = {
    "small_tank": 2,
    "supply_truck": 3,
    "small_plane": 3,
    "infantry": 10,
    "artillery": 2,
    "stealth_plane": 1,
    "sniper": 2,
    "anti_air": 4,
    "helicopter": 3,
    "attack_helicopter": 3,
    "bomber" : 1,
    "battle_ship": 1,
    "medium_tank": 5,
    "atv": 0

}

cards_in_deck = {
    "small_tank": 0,
    "supply_truck": 0,
    "small_plane": 0,
    "infantry": 0,
    "artillery": 0,
    "stealth_plane": 0,
    "sniper": 0,
    "anti_air": 0,
    "helicopter" : 0,
    "attack_helicopter": 0,
    "bomber" : 0,
    "battle_ship": 0,
    "medium_tank": 0,
    "atv": 0
}
