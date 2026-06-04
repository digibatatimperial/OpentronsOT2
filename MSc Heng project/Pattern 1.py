from opentrons import protocol_api
from opentrons.types import Point, Location
import math

metadata = {
    "protocolName": "Filter Paper Drop Casting: Red + Blue One Cycle",
    "author": "DIGIBAT Lab",
    "apiLevel": "2.15",
}

def run(protocol: protocol_api.ProtocolContext):

    # ============================================================
    # MODULES
    # ============================================================
    hs4 = protocol.load_module("heaterShakerModuleV1", 4)

    # Use this custom plate only as a coordinate reference on Zone 4.
    electrode_plate = hs4.load_labware(
        "digibat_1536_wellplate_1000ul",
        label="DIGIBAT 1536 Coordinate Reference"
    )

    # ============================================================
    # LABWARE
    # ============================================================
    rack20_6 = protocol.load_labware(
        "digibat_20ml_8_tube_rack",
        6
    )

    tips20_8 = protocol.load_labware(
        "opentrons_96_tiprack_20ul",
        8
    )

    # ============================================================
    # INSTRUMENT
    # ============================================================
    p20 = protocol.load_instrument(
        "p20_single_gen2",
        "right",
        tip_racks=[tips20_8]
    )

    # ============================================================
    # HEATER
    # ============================================================
    hs4.open_labware_latch()
    protocol.pause(
        "Place the filter paper on the top-left area of the hot plate. "
        "Align the intended first droplet position with the A1 reference position. "
        "Close the latch, then press RESUME."
    )
    hs4.close_labware_latch()

    hs4.set_target_temperature(70)
    hs4.wait_for_temperature()

    # ============================================================
    # SOURCES
    # ============================================================
    red_source = rack20_6["A1"]      # first vial, first row, red dye water
    blue_source = rack20_6["A2"]     # second vial, first row, blue dye water

    # ============================================================
    # FILTER PAPER GRID SETTINGS
    # ============================================================
    paper_x_mm = 65.0        # 6.5 cm
    paper_y_mm = 67.0        # 6.7 cm
    droplet_gap = 1.5        # mm spacing in both x and y

    drop_volume = 1.5        # µL per droplet
    z_height = 0.1           # mm above reference surface
    dwell_time = 0.15        # seconds after each droplet

    num_cycles = 1           # change to 50 later if needed

    # Small-batch dispensing settings
    batch_size = 5
    disposal_volume = 2.0
    source_aspirate_height = 30     # mm above source vial bottom

    p20.flow_rate.aspirate = 5
    p20.flow_rate.dispense = 3
    p20.flow_rate.blow_out = 10
    p20.default_speed = 150

    # ============================================================
    # BUILD GRID OVER FILTER PAPER
    # ============================================================

    # Use A1, A2, B1 to determine x/y directions of the labware coordinate system.
    a1 = electrode_plate["A1"].bottom(z_height).point
    a2 = electrode_plate["A2"].bottom(z_height).point
    b1 = electrode_plate["B1"].bottom(z_height).point

    x_vec = Point(
        x=a2.x - a1.x,
        y=a2.y - a1.y,
        z=0
    )
    y_vec = Point(
        x=b1.x - a1.x,
        y=b1.y - a1.y,
        z=0
    )

    x_len = math.sqrt(x_vec.x**2 + x_vec.y**2)
    y_len = math.sqrt(y_vec.x**2 + y_vec.y**2)

    x_unit = Point(x=x_vec.x / x_len, y=x_vec.y / x_len, z=0)
    y_unit = Point(x=y_vec.x / y_len, y=y_vec.y / y_len, z=0)

    n_x = int(paper_x_mm // droplet_gap) + 1
    n_y = int(paper_y_mm // droplet_gap) + 1

    actual_x_span = (n_x - 1) * droplet_gap
    actual_y_span = (n_y - 1) * droplet_gap

    margin_x = (paper_x_mm - actual_x_span) / 2
    margin_y = (paper_y_mm - actual_y_span) / 2

    # Optional offsets if the first droplet is not exactly where you want.
    # Positive x_shift moves along A1 -> A2 direction.
    # Positive y_shift moves along A1 -> B1 direction.
    x_shift_mm = 0.0
    y_shift_mm = 0.0

    start_point = Point(
        x=a1.x + (margin_x + x_shift_mm) * x_unit.x + (margin_y + y_shift_mm) * y_unit.x,
        y=a1.y + (margin_x + x_shift_mm) * x_unit.y + (margin_y + y_shift_mm) * y_unit.y,
        z=a1.z
    )

    target_locations = []

    for j in range(n_y):
        for i in range(n_x):
            point = Point(
                x=start_point.x + i * droplet_gap * x_unit.x + j * droplet_gap * y_unit.x,
                y=start_point.y + i * droplet_gap * x_unit.y + j * droplet_gap * y_unit.y,
                z=start_point.z
            )
            target_locations.append(Location(point, electrode_plate))

    protocol.comment(
        f"Generated {len(target_locations)} target droplets per pass "
        f"over {paper_x_mm} mm x {paper_y_mm} mm filter paper "
        f"with {droplet_gap} mm spacing."
    )

    # ============================================================
    # DISPENSING FUNCTION
    # ============================================================

    def cast_one_pass(source, source_name):
        protocol.comment(f"Starting one pass using {source_name}.")

        for start in range(0, len(target_locations), batch_size):
            batch = target_locations[start:start + batch_size]

            load_volume = len(batch) * drop_volume + disposal_volume

            p20.aspirate(
                load_volume,
                source.bottom(source_aspirate_height)
            )

            for target in batch:
                p20.dispense(drop_volume, target, rate=1.0)
                protocol.delay(seconds=dwell_time)

            # Return residual dead volume to the same source.
            p20.dispense(disposal_volume, source.top())

        p20.blow_out(source.top())
        protocol.comment(f"Completed one pass using {source_name}.")

    # ============================================================
    # RUN ONE CYCLE
    # ============================================================

    p20.pick_up_tip()

    # Pre-wet with red source first
    for _ in range(3):
        p20.aspirate(10, red_source.bottom(source_aspirate_height))
        p20.dispense(10, red_source.top())

    for cycle in range(num_cycles):
        protocol.comment(f"Starting cycle {cycle + 1} of {num_cycles}.")

        cast_one_pass(red_source, "red dye water from Zone 6 A1")
        cast_one_pass(blue_source, "blue dye water from Zone 6 A2")

        protocol.comment(f"Completed cycle {cycle + 1} of {num_cycles}.")

    p20.return_tip()

    hs4.deactivate_heater()

    protocol.comment("Filter paper red-blue drop-casting completed.")