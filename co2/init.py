"""
Initialize data storage
"""

import utils


if __name__ == "__main__":

    utils.init_csv("co2", ["temp_c", "temp_f", "temp_k", "co2_avg", "co2_raw", "co2_avg_npc", "co2_raw_npc", "pressure_mbar", "pressure_psi"])
