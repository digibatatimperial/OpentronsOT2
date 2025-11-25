import json

# DIGIBAT 384 Electrode Sheet parameters
ROWS = list("ABCDEFGHIJKLMNOP")  # 16 rows
COLS = list(range(1, 25))        # 24 columns

# Geometry from your measurements
X_OFFSET = 12.12
Y_OFFSET = 8.98
X_SPACING = 4.50
Y_SPACING = 4.50

# "Point" wells
WELL_DIAMETER = 1.0
WELL_DEPTH = 11.43
WELL_Z = 2.79
MAX_VOL = 112

# Build well dictionary
wells = {}
ordering = []

for col_index, col in enumerate(COLS):
    col_wells = []
    x = X_OFFSET + col_index * X_SPACING

    for row_index, row in enumerate(ROWS):
        well_name = f"{row}{col}"
        col_wells.append(well_name)

        y = Y_OFFSET + row_index * Y_SPACING

        wells[well_name] = {
            "depth": WELL_DEPTH,
            "totalLiquidVolume": MAX_VOL,
            "shape": "circular",
            "diameter": WELL_DIAMETER,
            "x": x,
            "y": y,
            "z": WELL_Z
        }

    ordering.append(col_wells)

# Assemble the labware definition
labware_def = {
    "version": 1,
    "schemaVersion": 2,
    "namespace": "digibat",
    "metadata": {
        "displayName": "DIGIBAT 384 Electrode Sheet",
        "displayCategory": "wellPlate",
        "displayVolumeUnits": "µL",
        "tags": ["electrode", "digibat", "sheet"]
    },
    "brand": {
        "brand": "DIGIBAT",
        "brandId": ["384-electrode-sheet"]
    },
    "parameters": {
        "format": "384Standard",
        "isTiprack": False,
        "isMagneticModuleCompatible": False,
        "loadName": "digibat_384_electrode_sheet"
    },
    "dimensions": {
        "xDimension": 127.76,
        "yDimension": 85.47,
        "zDimension": 14.22
    },
    "offset": {"x": 0, "y": 0, "z": 0},
    "wells": wells,
    "ordering": ordering,
    "cornerOffsetFromSlot": {"x": 0, "y": 0, "z": 0}
}

# Save file
outfile = "digibat_384_electrode_sheet.json"
with open(outfile, "w") as f:
    json.dump(labware_def, f, indent=2)

print(f"Saved: {outfile}")
