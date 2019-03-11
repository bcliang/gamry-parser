import gamry_parser as parser
import random

file = 'tests/cv_data.dta'
gp = parser.GamryParser()
gp.load(filename=file)
print('GamryParser() usage:')
print("experiment type: {}".format(gp.get_experiment_type()))
print("loaded curves: {}".format(gp.get_curve_count()))

curve_index = random.randint(1, gp.get_curve_count())
print("showing curve #{}".format(curve_index))
print(gp.get_curve_data(curve_index))

cv = parser.CyclicVoltammetry(filename=file)
cv.load()
print('\nCyclic Voltammetry class')
print("showing curve #{}".format(curve_index))
print(cv.get_curve_data(curve_index))
