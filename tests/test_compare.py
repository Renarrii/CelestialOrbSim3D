import unittest
import pandas as pd
import numpy as np
from datetime import timedelta, datetime
from src.compare_orbit import calculate_trajectory_errors

class TestTrajectoryAnalysis(unittest.TestCase):

    def test_calculate_trajectory_errors(self):
        # Setup mock simulation data
        base_time = datetime(2025, 7, 1)
        sim_data = pd.DataFrame({
            'Date': [base_time, base_time + timedelta(days=1)],
            'X': [0, 1000],
            'Y': [0, 0],
            'Z': [0, 0]
        })

        # Setup mock JPL data (slightly offset to generate a known error)
        jpl_data = {
            'times': np.array([base_time, base_time + timedelta(days=1)]),
            'x': np.array([0, 1000]),
            'y': np.array([3000, 4000]),  # 3km and 4km error in Y axis
            'z': np.array([4000, 3000])   # 4km and 3km error in Z axis
        }

        results = calculate_trajectory_errors(sim_data, jpl_data)

        # Distance calculation check: sqrt(3000^2 + 4000^2) = 5000 meters = 5.0 km
        self.assertEqual(len(results['errors_km']), 2)
        self.assertAlmostEqual(results['errors_km'][0], 5.0)
        self.assertAlmostEqual(results['errors_km'][1], 5.0)

if __name__ == "__main__":
    unittest.main()