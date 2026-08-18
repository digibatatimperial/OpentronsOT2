from opentrons import protocol_api
from opentrons.types import Point, Location
import math

metadata = {
    "protocolName": "Battery Electrode Slurry Drop Casting: Volume Screen RT + Heating",
    "author": "DIGIBAT Lab",
    "apiLevel": "2.15",}

def run(protocol: protocol_api.ProtocolContext):

    CASTING_TEMPERATURE_C = 37

    DROPLET_VOLUMES_UL = [100, 100, 100, 100, 100]

    REPLICATES_PER_VOLUME = 1

    FOIL_X_MM = 70.0
    FOIL_Y_MM = 70.0

    Z_HEIGHT_MM = 0.1


    SOURCE_ASPIRATE_HEIGHT_MM = 1.0

    ASPIRATE_RATE_UL_S = 10
    DISPENSE_RATE_UL_S = 19.2
    BLOWOUT_RATE_UL_S = 100      
    DELAY_AFTER_PIPETTING_S = 3

    X_SHIFT_MM = 0.0
    Y_SHIFT_MM = 0.0

    hs4 = protocol.load_module("heaterShakerModuleV1", 4)

    electrode_plate = hs4.load_labware(
        "digibat_1536_wellplate_1000ul",
        label="DIGIBAT 1536 Coordinate Reference")

    rack20_6 = protocol.load_labware(
        "digibat_20ml_8_tube_rack",
        6,
        label="20 mL Tube Rack for Battery Slurry")

    tips1000_8 = protocol.load_labware(
        "opentrons_96_tiprack_1000ul",
        8,
        label="1000 uL Tip Rack")

    p1000 = protocol.load_instrument(
        "p1000_single_gen2",
        "left",
        tip_racks=[tips1000_8])

    p1000.flow_rate.aspirate = ASPIRATE_RATE_UL_S
    p1000.flow_rate.dispense = DISPENSE_RATE_UL_S
    p1000.flow_rate.blow_out = BLOWOUT_RATE_UL_S
    p1000.default_speed = 80

    hs4.open_labware_latch()
    protocol.pause(
        "Place a clean, flat aluminium foil on the Heater-Shaker/hot plate. "
        "Align the intended top-left corner of the usable foil area with the A1 reference position. "
        "Fix the foil edges, close the latch, then press RESUME. ")

    hs4.close_labware_latch()

    hs4.set_target_temperature(CASTING_TEMPERATURE_C)
    hs4.wait_for_temperature()

    slurry_source = rack20_6["A1"]

    a1 = electrode_plate["A1"].bottom(Z_HEIGHT_MM).point
    a2 = electrode_plate["A2"].bottom(Z_HEIGHT_MM).point
    b1 = electrode_plate["B1"].bottom(Z_HEIGHT_MM).point

    x_vec = Point(x=a2.x - a1.x, y=a2.y - a1.y, z=0)
    y_vec = Point(x=b1.x - a1.x, y=b1.y - a1.y, z=0)

    x_len = math.sqrt(x_vec.x**2 + x_vec.y**2)
    y_len = math.sqrt(y_vec.x**2 + y_vec.y**2)

    x_unit = Point(x=x_vec.x / x_len, y=x_vec.y / x_len, z=0)
    y_unit = Point(x=y_vec.x / y_len, y=y_vec.y / y_len, z=0)

    foil_origin = Point(
        x=a1.x + X_SHIFT_MM * x_unit.x + Y_SHIFT_MM * y_unit.x,
        y=a1.y + X_SHIFT_MM * x_unit.y + Y_SHIFT_MM * y_unit.y,
        z=a1.z)

    def local_point_to_location(local_x_mm, local_y_mm):
        point = Point(
            x=foil_origin.x + local_x_mm * x_unit.x + local_y_mm * y_unit.x,
            y=foil_origin.y + local_x_mm * x_unit.y + local_y_mm * y_unit.y,
            z=foil_origin.z)
        return Location(point, electrode_plate)

    if REPLICATES_PER_VOLUME != 1:
        raise ValueError(
            "This template is configured for 1 replicate per volume on a 65 x 50 mm foil. "
            "For triplicates, use three separate foils/runs or enlarge the foil area and manually define 15 positions.")

    positions_mm = [
        (FOIL_X_MM * 0.18, FOIL_Y_MM * 0.30),  
        (FOIL_X_MM * 0.50, FOIL_Y_MM * 0.30),  
        (FOIL_X_MM * 0.82, FOIL_Y_MM * 0.30),  
        (FOIL_X_MM * 0.34, FOIL_Y_MM * 0.72),  
        (FOIL_X_MM * 0.66, FOIL_Y_MM * 0.72), ]

    droplet_targets = []
    for volume_ul, (x_mm, y_mm) in zip(DROPLET_VOLUMES_UL, positions_mm):
        droplet_targets.append((volume_ul, local_point_to_location(x_mm, y_mm), x_mm, y_mm))

    protocol.comment(
        f"Single-droplet test: {DROPLET_VOLUMES_UL} µL, one spot per electrode. "
        f"Casting at {CASTING_TEMPERATURE_C} °C, then drying at room temperature until no visible solvent remains.")

    p1000.pick_up_tip()

    for _ in range(3):
        p1000.aspirate(300, slurry_source.bottom(SOURCE_ASPIRATE_HEIGHT_MM), rate=1.0)
        protocol.delay(seconds=1)
        p1000.dispense(300, slurry_source.top(), rate=1.0)
        protocol.delay(seconds=1)

    for volume_ul, target, x_mm, y_mm in droplet_targets:
        protocol.comment(f"Dispensing {volume_ul} µL slurry at local position x={x_mm:.1f} mm, y={y_mm:.1f} mm.")

        p1000.aspirate(volume_ul, slurry_source.bottom(SOURCE_ASPIRATE_HEIGHT_MM), rate=1.0)
        protocol.delay(seconds=DELAY_AFTER_PIPETTING_S)

        p1000.dispense(volume_ul, target, rate=1.0)
        protocol.delay(seconds=DELAY_AFTER_PIPETTING_S)

        p1000.blow_out(target)
        protocol.delay(seconds=DELAY_AFTER_PIPETTING_S)

    p1000.return_tip()

    protocol.comment(
        f"Drop-casting complete at {CASTING_TEMPERATURE_C} °C. "
        "Deactivating heater for passive cooling / room-temperature drying.")

    hs4.deactivate_heater()

    protocol.pause(
        "The heater has been deactivated. "
        "Let the electrodes cool and dry at room temperature until no visible solvent remains. "
        "When the electrodes appear dry, press RESUME to finish the protocol.")

    protocol.comment(
        f"Single-droplet electrode drying completed. "
        f"Casting temperature: {CASTING_TEMPERATURE_C} °C; final drying: heater deactivated / room-temperature drying.")
