from opentrons import protocol_api

metadata = {
    "protocolName": "DIGIBAT – Drop Casting (384 Electrode Sheet, 2 µL × 384) – Final",
    "author": "DIGIBAT Lab",
    "apiLevel": "2.15",
}

def run(protocol: protocol_api.ProtocolContext):

    # ============================================================
    # MODULES
    # ============================================================
    # Slot 4 — Heater–Shaker
    hs4 = protocol.load_module("heaterShakerModuleV1", 4)

    # Load your custom DIGIBAT 384 electrode sheet *directly* on the module
    electrode_plate = hs4.load_labware(
        "digibat_384_wellplate_1000ul",
        label="DIGIBAT 384 Electrode Sheet"
    )

    # Slot 10 — additional Heater–Shaker (present but UNUSED)
    protocol.load_module("heaterShakerModuleV1", 10)

    # ============================================================
    # LABWARE
    # ============================================================
    # Slot 1 — HPLC 40-vial rack
    hplc_1 = protocol.load_labware(
        "digibathplc2ml40vials_40_tuberack_2000ul", 1
    )

    # Slot 2 — HPLC 40-vial rack
    hplc_2 = protocol.load_labware(
        "digibathplc2ml40vials_40_tuberack_2000ul", 2
    )

    # Slot 3 — DIGIBAT 20 mL 8-tube rack
    rack20_3 = protocol.load_labware("digibat_20ml_8_tube_rack", 3)

    # Slot 6 — DIGIBAT 20 mL 8-tube rack (ink source in A1)
    rack20_6 = protocol.load_labware("digibat_20ml_8_tube_rack", 6)

    # Slot 7 — empty
    # Slot 11 — empty

    # ============================================================
    # TIP RACKS
    # ============================================================
    tips1000_9 = protocol.load_labware("opentrons_96_tiprack_1000ul", 9)
    tips20_8 = protocol.load_labware("opentrons_96_tiprack_20ul", 8)

    # ============================================================
    # INSTRUMENTS
    # ============================================================
    p20 = protocol.load_instrument(
        "p20_single_gen2",
        "right",
        tip_racks=[tips20_8]
    )

    p1000 = protocol.load_instrument(
        "p1000_single_gen2",
        "left",
        tip_racks=[tips1000_9]
    )

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
        name="Ink / Water",
        description="10 mL Ink/Water in slot 6 A1 (source for drop casting)",
        display_color="#4AA3E0"
    )
    rack20_6["A1"].load_liquid(water_6A1, volume=10000)

    # ============================================================
    # HEATER–SHAKER WORKFLOW
    # ============================================================
    hs4.open_labware_latch()
    protocol.pause(
        "Place the DIGIBAT 384 Electrode Sheet (custom labware) on the Heater–Shaker in Slot 4. "
        "Close the latch, then press RESUME."
    )
    hs4.close_labware_latch()

    hs4.set_target_temperature(50)
    hs4.wait_for_temperature()

    # (Optional) shaking if needed:
    # hs4.set_and_wait_for_shake_speed(500)

    # ============================================================
    # DROP CASTING — DISTRIBUTE 2 µL TO ALL 384 POSITIONS
    # ============================================================
    source = rack20_6["A1"]
    destination_wells = list(electrode_plate.wells())   # 384 positions

    dist_volume = 10      # 2 µL per spot
    load_volume = 500    # aspirate 200 µL at a time into P1000

    p1000.pick_up_tip()
    remaining = 0

    for dest in destination_wells:
        # Reload from source if not enough volume left in the tip
        if remaining < dist_volume:
            p1000.aspirate(load_volume, source.bottom(1.5))
            remaining = load_volume

        # Dispense 2 µL onto the electrode sheet
        p1000.dispense(dist_volume, dest.bottom(0.5))
        remaining -= dist_volume

    # Clear any residual liquid from the tip
    p1000.blow_out(source.top())
    p1000.drop_tip()

    protocol.comment("DIGIBAT 384-electrode-sheet drop-casting (2 µL per position) completed successfully.")
