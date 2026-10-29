from front.file_handler import SimulationLogger as SL

params = {"N": 108, "density": 0.8, "T_star": 1.2, "dt": 0.005}
SL(".", "file_handler_test.h5", 100, params=params)
