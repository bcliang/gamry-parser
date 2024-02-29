import os
import gamry_parser as parser
import random

file = os.path.join("tests", "test_data", "cv_data.dta")
gp = parser.GamryParser()
gp.load(filename=file)
print("GamryParser() usage:")
print("experiment type: {}".format(gp.experiment_type))
print("loaded curves: {}".format(gp.curve_count))

curve_index = random.randint(0, gp.curve_count - 1)
print("showing curve #{}".format(curve_index))
print(gp.curve(curve_index))

cv = parser.CyclicVoltammetry(filename=file)
cv.load()
vrange = cv.v_range
print("\nCyclic Voltammetry class")
print("Programmed Scan Rate: {} mV/s".format(cv.scan_rate))
print("Programmed V range: [{}, {}] V".format(vrange[0], vrange[1]))
print(
    "\tnote: range will not match with below; the raw file has been modified for faster test execution"
)

curve = cv.curve(curve_index)
print("showing curve #{}".format(curve_index))
print("Acheived V range: [{}, {}]".format(min(curve["Vf"]), max(curve["Vf"])))
print(curve)
