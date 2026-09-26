"""Read a cyclic voltammetry file with gamry-parser."""

from pathlib import Path

import gamry_parser as gp

path = Path(__file__).parent / "tests" / "data" / "cv_data.dta"
cv = gp.CyclicVoltammetry.read(path)

print(f"{path.name}: {cv.experiment_type}, {cv.curve_count} curves, started {cv.start_time}")
print(f"programmed scan rate: {cv.scan_rate} mV/s, limits: {cv.v_range} V")

curve = cv.curve(2)
print("extracted (V, I) from `cv.curve(2)`:")
print(f"curve 2 potential range: [{curve['Vf'].min()}, {curve['Vf'].max()}] V")
print(curve)

curve_full = cv.curves[2]
print("full curve from `cv.curves[2]`:")
print(curve_full)
