from opentrons import protocol_api
from opentrons.types import Point, Location

metadata = {
    "protocolName": "DIGIBAT – Drop Casting (1536 Electrode Sheet, 3×2 µL per well, P1000)",
    "author": "DIGIBAT Lab",
    "apiLevel": "2.15",
}

def run(protocol: protocol_api.ProtocolContext):

    # ============================================================
    # MODULES
    # ============================================================
    # Slot 4 — Heater–Shaker
    hs4 = protocol.load_module("heaterShakerModuleV1", 4)

    # Load your custom DIGIBAT 1536 electrode sheet directly on the module
    # NOTE: API name must match your custom labware JSON
    electrode_plate = hs4.load_labware(
        "digibat_1536_wellplate_1000ul",   # <--- your labware API name
        label="DIGIBAT 1536 Electrode Sheet"
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

    # Optional: starting tip for P1000
    p1000.starting_tip = tips1000_9.wells_by_name()["A1"]

    # (Optional) slightly slower dispense to help tiny volumes leave the tip
    # p1000.flow_rate.dispense = 5

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
        "Place the DIGIBAT 1536 Electrode Sheet (labware "
        "'digibat_1546_wellplate_1000ul') on the Heater–Shaker in Slot 4. "
        "Close the latch, then press RESUME."
    )
    hs4.close_labware_latch()

    hs4.set_target_temperature(50)
    hs4.wait_for_temperature()

    # (Optional) shaking if needed:
    # hs4.set_and_wait_for_shake_speed(500)
    # hs4.deactivate_shaker()

    # ============================================================
    # DROP CASTING — 3 PASSES, P1000, LOAD 500 µL EACH TIME
    # ============================================================
    source = rack20_6["A1"]
    destination_wells = list(electrode_plate.wells())   # 1536 wells

    dist_volume = 4       # 2 µL per droplet per pass
    load_volume = 500     # aspirate 500 µL at a time (P1000)
    num_passes = 1        # total passes => 3 droplets per well (6 µL total)

    # Use one tip for all passes
    p1000.pick_up_tip()

    for pass_index in range(num_passes):
        protocol.comment(f"Starting pass {pass_index + 1} of {num_passes} over 1536 wells.")

        remaining = 0.0   # track the volume left in the tip (software-side)

        for dest in destination_wells:
            # If not enough volume left in the tip for next dispense,
            # first dump any leftover, then aspirate a fresh 500 µL
            if remaining < dist_volume:
                if remaining > 0:
                    # dump remaining back to source top (or a waste well)
                    p1000.dispense(remaining, source.top())
                    remaining = 0.0

                p1000.aspirate(load_volume, source.bottom(1.5))
                remaining = float(load_volume)

            # Dispense 2 µL into the well, low height to help droplet detach
            p1000.dispense(dist_volume, dest.bottom(0.5))
            remaining -= dist_volume

            # Optional: help droplet release (comment out if too slow)
            # p1000.touch_tip(dest, v_offset=-1.0, speed=20)

        # End of this pass: dump any leftover volume and reset
        if remaining > 0:
            p1000.dispense(remaining, source.top())
            remaining = 0.0

        # Optional: brief shake between passes
        # hs4.set_and_wait_for_shake_speed(300)
        # hs4.deactivate_shaker()

    # Clear any residual liquid, KEEP the tip
    p1000.air_gap(10)
    p1000.blow_out(source.top())

    # Do NOT drop the tip; keep it for later if needed
    # p1000.drop_tip()

    # Optionally cool down / stop heater–shaker
    hs4.deactivate_heater()
    # hs4.deactivate_shaker()

    protocol.comment(
        "DIGIBAT 1536-electrode-sheet drop-casting completed: "
        "3 passes, 2 µL per well per pass (total 6 µL per well), "
        "using P1000 with 500 µL loads. Tip retained on the pipette."
    )
