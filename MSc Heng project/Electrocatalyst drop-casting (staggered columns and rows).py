from opentrons import protocol_api
from opentrons.types import Point, Location
import math

metadata = {"protocolName": "Filter Paper Drop Casting: Ink One Cycle",
    "author": "DIGIBAT Lab",
    "apiLevel": "2.15",}

def run(protocol: protocol_api.ProtocolContext):

    # ============================================================
    # MODULES
    # ============================================================
    hs4 = protocol.load_module("heaterShakerModuleV1", 4)

    # Use this custom plate only as a coordinate reference on Zone 4.
    electrode_plate = hs4.load_labware(
        "digibat_1536_wellplate_1000ul",
        label="DIGIBAT 1536 Coordinate Reference")

    # ============================================================
    # LABWARE
    # ============================================================
    rack20_6 = protocol.load_labware(
        "digibat_20ml_8_tube_rack", 6)

    tips20_8 = protocol.load_labware(
        "opentrons_96_tiprack_20ul", 8)

    # ============================================================
    # INSTRUMENT
    # ============================================================
    p20 = protocol.load_instrument(
        "p20_single_gen2",
        "right",
        tip_racks=[tips20_8])

    # ============================================================
    # HEATER
    # ============================================================
    hs4.open_labware_latch()
    protocol.pause(
        "Place the filter paper on the top-left area of the hot plate. "
        "Align the intended first droplet position with the A1 reference position. "
        "Close the latch, then press RESUME.")
    hs4.close_labware_latch()
    hs4.set_target_temperature(70)
    hs4.wait_for_temperature()

    # ============================================================
    # SOURCES
    # ============================================================
    ink_source = rack20_6["A1"]      # ink source for both layers
    # ============================================================
    # FILTER PAPER GRID SETTINGS
    # ============================================================
    paper_x_mm = 60.0        # length in mm
    paper_y_mm = 60.0        # width in mm
    droplet_gap = 2.0        # mm spacing in both x and y, taking 2, 2.5 or 3 mm in different tests
    drop_volume = 4.0        # µL per droplet
    z_height = 0.1           # mm above reference surface
    dwell_time = 0.15        # seconds after each droplet
    num_cycles = 1           # change to a large number depending on loadingneeds

    # Small-batch dispensing settings
    batch_size = 4
    disposal_volume = 2.0
    source_aspirate_height =1.0
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
        z=0)

    y_vec = Point(
        x=b1.x - a1.x,
        y=b1.y - a1.y,
        z=0)

    x_len = math.sqrt(x_vec.x**2 + x_vec.y**2)
    y_len = math.sqrt(y_vec.x**2 + y_vec.y**2)
    x_unit = Point(x=x_vec.x / x_len, y=x_vec.y / x_len, z=0)
    y_unit = Point(x=y_vec.x / y_len, y=y_vec.y / y_len, z=0)
    n_x_layer1 = int(paper_x_mm // droplet_gap) + 1
    n_y_layer1 = int(paper_y_mm // droplet_gap) + 1

    n_x_layer2 = n_x_layer1 - 1
    n_y_layer2 = n_y_layer1 - 1
    actual_x_span_layer1 = (n_x_layer1 - 1) * droplet_gap
    actual_y_span_layer1 = (n_y_layer1 - 1) * droplet_gap
    margin_x = (paper_x_mm - actual_x_span_layer1) / 2
    margin_y = (paper_y_mm - actual_y_span_layer1) / 2

    x_shift_mm = 0.0
    y_shift_mm = 0.0

    start_point_layer1 = Point(
        x=a1.x + (margin_x + x_shift_mm) * x_unit.x + (margin_y + y_shift_mm) * y_unit.x,
        y=a1.y + (margin_x + x_shift_mm) * x_unit.y + (margin_y + y_shift_mm) * y_unit.y,
        z=a1.z)

    start_point_layer2 = Point(
        x=start_point_layer1.x
          + (droplet_gap / 2) * x_unit.x
          + (droplet_gap / 2) * y_unit.x,
        y=start_point_layer1.y
          + (droplet_gap / 2) * x_unit.y
          + (droplet_gap / 2) * y_unit.y,
        z=start_point_layer1.z)

    def build_grid(start_point, n_x, n_y, layer_name):
        locations = []

        # 1-based odd rows first: row 1, 3, 5...
        # Then 1-based even rows: row 2, 4, 6...
        row_order = list(range(0, n_y, 2)) + list(range(1, n_y, 2))

        for j in row_order:
            # Within each row:
            # 1-based odd columns first: column 1, 3, 5...
            # Then 1-based even columns: column 2, 4, 6...
            column_order = list(range(0, n_x, 2)) + list(range(1, n_x, 2))

            for i in column_order:
                point = Point(
                    x=start_point.x + i * droplet_gap * x_unit.x + j * droplet_gap * y_unit.x,
                    y=start_point.y + i * droplet_gap * x_unit.y + j * droplet_gap * y_unit.y,
                    z=start_point.z)
                locations.append(Location(point, electrode_plate))

        protocol.comment(
            f"{layer_name}: generated {len(locations)} droplets "
            f"({n_x} x {n_y}) with {droplet_gap} mm spacing. "
            "Order: odd rows first, then even rows; within each row, odd columns first, then even columns.")

        return locations

    target_locations_layer1 = build_grid(
        start_point_layer1,
        n_x_layer1,
        n_y_layer1,
        "Layer 1")

    target_locations_layer2 = build_grid(
        start_point_layer2,
        n_x_layer2,
        n_y_layer2,
        "Layer 2, x- and y-offset by half gap")

    # ============================================================
    # DISPENSING FUNCTION
    # ============================================================

    def cast_one_pass(source, source_name, locations):
        protocol.comment(
            f"Starting one pass using {source_name}, "
            f"{len(locations)} target locations.")

        for start in range(0, len(locations), batch_size):
            batch = locations[start:start + batch_size]

            load_volume = len(batch) * drop_volume + disposal_volume

            p20.aspirate(
                load_volume,
                source.bottom(source_aspirate_height))

            for target in batch:
                p20.dispense(drop_volume, target, rate=1.0)
                protocol.delay(seconds=dwell_time)

            # Return residual dead volume to the same source and clear the tip.
            p20.dispense(disposal_volume, source.top())
            p20.blow_out(source.top())

        p20.blow_out(source.top())
        protocol.comment(f"Completed one pass using {source_name}.")

    p20.pick_up_tip()

    # Pre-wet with red source first
    # Pre-wet with ink source
    for _ in range(3):
        p20.aspirate(10, ink_source.bottom(source_aspirate_height))
        p20.dispense(10, ink_source.top())

    for cycle in range(num_cycles):
        protocol.comment(f"Starting cycle {cycle + 1} of {num_cycles}.")

        # Layer 1: ink, no offset
        cast_one_pass(
            ink_source,
            "Layer 1 ink from Zone 6 A1",
            target_locations_layer1)

        # Layer 2: ink, x-offset and y-offset by half droplet gap
        cast_one_pass(
            ink_source,
            "Layer 2 ink from Zone 6 A1, x- and y-offset by half gap",
            target_locations_layer2)

        protocol.comment(f"Completed cycle {cycle + 1} of {num_cycles}.")

    p20.drop_tip()
    hs4.deactivate_heater()
    protocol.comment("Pattern 3 test on 60 mm x 60 mm filter paper completed.")