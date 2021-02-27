import gamry_parser as parser
import random

file = "tests/cv_data.dta"
gp = parser.GamryParser()
gp.load(filename=file)
print("GamryParser() usage:")
print("experiment type: {}".format(gp.get_experiment_type()))
print("loaded curves: {}".format(gp.get_curve_count()))

curve_index = random.randint(1, gp.get_curve_count())
print("showing curve #{}".format(curve_index))
print(gp.get_curve_data(curve_index))

cv = parser.CyclicVoltammetry(filename=file)
cv.load()
vrange = cv.get_v_range()
print("\nCyclic Voltammetry class")
print("Programmed Scan Rate: {} mV/s".format(cv.get_scan_rate()))
print("Programmed V range: [{}, {}] V".format(vrange[0], vrange[1]))
print(
    "\tnote: range will not match with below; the raw file has been modified for faster test execution"
)

curve = cv.get_curve_data(curve_index)
print("showing curve #{}".format(curve_index))
print("Acheived V range: [{}, {}]".format(min(curve["Vf"]), max(curve["Vf"])))
print(curve)
