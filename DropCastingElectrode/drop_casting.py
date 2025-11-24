from opentrons import protocol_api

metadata = {
    "protocolName": "DIGIBAT – Drop Casting (384-well, 2 µL × 384) – Final",
    "author": "DIGIBAT Lab",
    "apiLevel": "2.15"
}

def run(protocol: protocol_api.ProtocolContext):

    # ============================================================
    # MODULES
    # ============================================================
    hs4 = protocol.load_module("heaterShakerModuleV1", 4)
    flat_adapter = hs4.load_adapter("opentrons_universal_flat_adapter")
    plate_384 = flat_adapter.load_labware("corning_384_wellplate_112ul_flat")

    # Slot 10 has a heater-shaker but unused
    protocol.load_module("heaterShakerModuleV1", 10)

    # ============================================================
    # LABWARE
    # ============================================================
    hplc_1 = protocol.load_labware("digibathplc2ml40vials_40_tuberack_2000ul", 1)
    hplc_2 = protocol.load_labware("digibathplc2ml40vials_40_tuberack_2000ul", 2)

    rack20_3 = protocol.load_labware("digibat_20ml_8_tube_rack", 3)
    rack20_6 = protocol.load_labware("digibat_20ml_8_tube_rack", 6)

    # Slot 7 empty
    # Slot 11 empty

    # ============================================================
    # TIP RACKS
    # ============================================================
    tips1000_9 = protocol.load_labware("opentrons_96_tiprack_1000ul", 9)
    tips20_8 = protocol.load_labware("opentrons_96_tiprack_20ul", 8)

    # ============================================================
    # INSTRUMENTS
    # ============================================================
    p20 = protocol.load_instrument("p20_single_gen2", "right", tip_racks=[tips20_8])
    p1000 = protocol.load_instrument("p1000_single_gen2", "left", tip_racks=[tips1000_9])

    # Start 1000 µL pipette at tip C11
    p1000.starting_tip = tips1000_9.wells_by_name()["C11"]

    # ============================================================
    # LIQUID DEFINITIONS
    # ============================================================
    water_3A1 = protocol.define_liquid(
        name="Water",
        description="10 mL Water in slot 3 A1",
        display_color="#4AA3E0"
    )
    rack20_3["A1"].load_liquid(water_3A1, volume=10000)

    water_6A1 = protocol.define_liquid(
        name="Water",
        description="10 mL Water in slot 6 A1",
        display_color="#4AA3E0"
    )
    rack20_6["A1"].load_liquid(water_6A1, volume=10000)

    # ============================================================
    # HEATER–SHAKER WORKFLOW
    # ============================================================
    hs4.open_labware_latch()
    protocol.pause("Place the 384-well plate on the Heater-Shaker (Slot 4). Close the latch then press RESUME.")
    hs4.close_labware_latch()

    hs4.set_target_temperature(50)
    hs4.wait_for_temperature()

    # ============================================================
    # DROP CASTING — DISTRIBUTE 2 µL TO ALL 384 WELLS
    # ============================================================
    source = rack20_6["A1"]
    destination_wells = [well for well in plate_384.wells()]  # 384 wells

    dist_volume = 2       # 2 µL per well  
    load_volume = 200     # pick up 200 µL at once

    p1000.pick_up_tip()

    remaining = 0

    for dest in destination_wells:
        if remaining < dist_volume:
            # need to reload source
            p1000.aspirate(load_volume, source.bottom(3))
            remaining = load_volume

        p1000.dispense(dist_volume, dest.bottom(1))
        remaining -= dist_volume

    p1000.blow_out(source.top())
    p1000.drop_tip()

    protocol.comment("DIGIBAT 384-well drop-casting (2 µL per well) completed successfully.")
