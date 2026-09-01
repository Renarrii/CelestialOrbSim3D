import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
from typing import Dict, Any, Optional
from astroquery.jplhorizons import Horizons
from astropy.time import Time

# --- Constants
AU_TO_METERS: float = 1.495978707e11
METERS_TO_KM: float = 1000.0
MAX_TIME_DIFF_SECONDS: float = 86400.0  # 1 day
JPL_TARGET_ID: str = '3I'
SIMULATION_FILE_PATH: str = 'atlas_simulated_trajectory_rk4.csv'


def load_simulation_data(file_path: str) -> Optional[pd.DataFrame]:
    """Loads simulation data from a CSV file and parses dates."""
    try:
        df = pd.read_csv(file_path)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found. Run the simulation first.")
        return None


def fetch_jpl_ephemeris(start_date: datetime, end_date: datetime, target_id: str) -> Optional[Dict[str, np.ndarray]]:
    """Fetches real ephemeris data from JPL Horizons for the specified date range."""
    epochs_dict = {
        'start': start_date.strftime('%Y-%m-%d'),
        'stop': (end_date + timedelta(days=1)).strftime('%Y-%m-%d'),
        'step': '1d'
    }

    try:
        obj = Horizons(id=target_id, location='@0', epochs=epochs_dict)
        vecs = obj.vectors()

        # Convert Julian Dates to standard Python datetimes (naive)
        times = Time(vecs['datetime_jd'], format='jd').to_datetime()
        times_naive = np.array([t.replace(tzinfo=None) for t in times])

        return {
            'times': times_naive,
            'x': vecs['x'] * AU_TO_METERS,
            'y': vecs['y'] * AU_TO_METERS,
            'z': vecs['z'] * AU_TO_METERS
        }
    except Exception as e:
        print(f"Error fetching data from JPL Horizons: {e}")
        return None


def calculate_trajectory_errors(sim_df: pd.DataFrame, jpl_data: Dict[str, np.ndarray]) -> Dict[str, list]:
    """Compares simulated coordinates with JPL data and calculates Euclidean errors."""
    analysis_results: Dict[str, Any] = {
        'dates': [],
        'errors_km': [],
        'sim_coords': {'x': [], 'y': [], 'z': []},
        'jpl_coords': {'x': [], 'y': [], 'z': []}
    }

    for i, jpl_time in enumerate(jpl_data['times']):
        # Find the simulation row with the closest timestamp
        time_diffs = abs(sim_df['Date'] - jpl_time)
        best_idx = time_diffs.idxmin()

        # Skip if the closest frame is too far in time (e.g. gap in simulation)
        if time_diffs[best_idx].total_seconds() > MAX_TIME_DIFF_SECONDS:
            continue

        closest_sim_row = sim_df.loc[best_idx]
        sim_pos = (closest_sim_row['X'], closest_sim_row['Y'], closest_sim_row['Z'])
        jpl_pos = (jpl_data['x'][i], jpl_data['y'][i], jpl_data['z'][i])

        # Calculate Euclidean distance in meters, convert to kilometers
        dist_m = np.sqrt(
            (jpl_pos[0] - sim_pos[0]) ** 2 +
            (jpl_pos[1] - sim_pos[1]) ** 2 +
            (jpl_pos[2] - sim_pos[2]) ** 2
        )

        analysis_results['dates'].append(jpl_time)
        analysis_results['errors_km'].append(dist_m / METERS_TO_KM)

        analysis_results['sim_coords']['x'].append(sim_pos[0])
        analysis_results['sim_coords']['y'].append(sim_pos[1])
        analysis_results['sim_coords']['z'].append(sim_pos[2])

        analysis_results['jpl_coords']['x'].append(jpl_pos[0])
        analysis_results['jpl_coords']['y'].append(jpl_pos[1])
        analysis_results['jpl_coords']['z'].append(jpl_pos[2])

    return analysis_results


def plot_results(analysis_data: Dict[str, list]) -> None:
    """Renders the position error plot and 3D trajectory plot."""
    fig = plt.figure(figsize=(14, 6))

    # --- PLOT 1: Error Accumulation ---
    ax1 = fig.add_subplot(1, 2, 1)
    ax1.plot(analysis_data['dates'], analysis_data['errors_km'], color='red', linewidth=2)
    ax1.set_title("Simulation vs JPL (Position Error)")
    ax1.set_xlabel("Simulation Date")
    ax1.set_ylabel("Error [km]")
    ax1.grid(True)
    ax1.tick_params(axis='x', rotation=45)

    # --- PLOT 2: 3D Trajectory ---
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    m_to_au = 1 / AU_TO_METERS  # Convert back to AU for chart readability

    ax2.plot(np.array(analysis_data['jpl_coords']['x']) * m_to_au,
             np.array(analysis_data['jpl_coords']['y']) * m_to_au,
             np.array(analysis_data['jpl_coords']['z']) * m_to_au,
             label="True Orbit (JPL)", color='blue', linestyle='--')

    ax2.plot(np.array(analysis_data['sim_coords']['x']) * m_to_au,
             np.array(analysis_data['sim_coords']['y']) * m_to_au,
             np.array(analysis_data['sim_coords']['z']) * m_to_au,
             label="Your Simulation", color='orange', alpha=0.8)

    ax2.scatter(0, 0, 0, color='yellow', s=100, label="Sun")

    ax2.set_title("Trajectory: Simulation vs Reality")
    ax2.set_xlabel("X [AU]")
    ax2.set_ylabel("Y [AU]")
    ax2.set_zlabel("Z [AU]")
    ax2.legend()

    plt.tight_layout()
    plt.show()


def main() -> None:
    print("1. Loading simulation data...")
    sim_df = load_simulation_data(SIMULATION_FILE_PATH)
    if sim_df is None:
        return

    start_date = sim_df['Date'].min()
    end_date = sim_df['Date'].max()
    print(f"Simulation data range: {start_date} to {end_date}")

    if (end_date - start_date).days < 1:
        print("Simulation covers less than 1 day. Run it longer for meaningful comparisons.")
        return

    print("2. Fetching real ephemeris data from JPL Horizons...")
    jpl_data = fetch_jpl_ephemeris(start_date, end_date, JPL_TARGET_ID)
    if jpl_data is None:
        return

    print("3. Analyzing errors (matching timestamps)...")
    analysis_results = calculate_trajectory_errors(sim_df, jpl_data)

    if not analysis_results['dates']:
        print("Could not match any simulation dates with JPL dates.")
        return

    print("4. Generating plots...")
    plot_results(analysis_results)

if __name__ == "__main__":
    main()