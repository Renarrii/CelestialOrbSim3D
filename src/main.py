import csv
from typing import List, Optional
from datetime import datetime, timedelta
import vpython as vp
from astroquery.jplhorizons import Horizons

# Physical and configuration constants
TIME_STEP_SECONDS: float = 1000.0
AU_TO_METERS: float = 1.495978707e11
DAYS_TO_SECONDS: float = 86400.0
STEPS_PER_SAVE: int = 100

JPL_BODY_IDS = {
    "Sun": "10",
    "Mercury": "199",
    "Venus": "299",
    "Earth": "399",
    "Moon": "301",
    "Mars": "499",
    "Jupiter": "599",
    "Saturn": "699",
    "Uranus": "799",
    "Neptune": "899",
    "3I/ATLAS": "3I"
}


class CelestialBody:
    """Represents a celestial body in the simulation."""

    def __init__(self, name: str, mu: float, pos: vp.vector, vel: vp.vector,
                 radius: float, color: vp.vector, make_trail: bool = True):
        self.name: str = name
        self.mu: float = mu
        self.vel: vp.vector = vel
        self.sphere = vp.sphere(pos=pos, radius=radius, color=color, make_trail=make_trail)
    @property
    def pos(self) -> vp.vector:
        return self.sphere.pos

    @pos.setter
    def pos(self, value: vp.vector) -> None:
        self.sphere.pos = value


def setup_solar_system() -> List[CelestialBody]:
    """Initializes default parameters for celestial bodies using precise GM (mu) values."""
    earth_pos = vp.vector(1.496e11, 0, 0)
    earth_vel = vp.vector(0, 29780, 0)

    return [
        CelestialBody("Sun", 1.32712440042e20, vp.vector(0, 0, 0), vp.vector(0, 0, 0), 1e10, vp.color.yellow, False),
        CelestialBody("Mercury", 2.2032e13, vp.vector(5.79e10, 0, 0), vp.vector(0, 47360, 0), 1e9, vp.color.gray(0.5)),
        CelestialBody("Venus", 3.24859e14, vp.vector(1.082e11, 0, 0), vp.vector(0, 35020, 0), 3e8, vp.color.orange),
        CelestialBody("Earth", 3.98600435436e14, earth_pos, earth_vel, 3e8, vp.color.blue),
        CelestialBody("Moon", 4.902800e12, earth_pos + vp.vector(3.844e8, 0, 0), earth_vel + vp.vector(0, 1022, 0), 5e7, vp.color.white),
        CelestialBody("Mars", 4.282837e13, vp.vector(2.279e11, 0, 0), vp.vector(0, 24070, 0), 2e8, vp.color.red),
        CelestialBody("Jupiter", 1.26686534e17, vp.vector(-7.785e11, 0, 0), vp.vector(0, -13070, 0), 7e9, vp.color.magenta),
        CelestialBody("Saturn", 3.7931187e16, vp.vector(-1.432e12, 0, 0), vp.vector(0, -9680, 0), 6e9, vp.color.white),
        CelestialBody("Uranus", 5.793939e15, vp.vector(2.867e12, 0, 0), vp.vector(0, 6800, 0), 4e9, vp.color.cyan),
        CelestialBody("Neptune", 6.836527e15, vp.vector(4.515e12, 0, 0), vp.vector(0, 5430, 0), 4e9, vp.color.purple),
        CelestialBody("3I/ATLAS", 6.674e3, vp.vector(6.0e11, 6.0e11, 0), vp.vector(-20000, -25000, 0), 2e8, vp.color.green)
    ]

def fetch_jpl_ephemeris(date_str: str) -> dict:
    """Constructs the epochs dictionary required by the JPL Horizons API."""
    try:
        d_start = datetime.strptime(date_str, '%Y-%m-%d')
        d_stop = d_start + timedelta(days=1)
        return {
            'start': d_start.strftime('%Y-%m-%d'),
            'stop': d_stop.strftime('%Y-%m-%d'),
            'step': '1d'
        }
    except ValueError as err:
        raise ValueError("Invalid date format. Use 'YYYY-MM-DD'.") from err


def update_positions_from_date(bodies: List[CelestialBody], date_str: str) -> None:
    """Fetches positions and velocities of bodies for a given date from JPL Horizons."""
    print(f"Fetching ephemeris data for the date: {date_str}...")

    try:
        epochs_dict = fetch_jpl_ephemeris(date_str)
    except ValueError as e:
        print(f"Error: {e}")
        return

    for body in bodies:
        if body.name not in JPL_BODY_IDS:
            print(f"Skipped {body.name} (no JPL ID defined).")
            continue

        try:
            obj = Horizons(id=JPL_BODY_IDS[body.name], location='@0', epochs=epochs_dict)
            vectors = obj.vectors()

            # Convert Astronomical Units (AU) to meters and (AU/d) to (m/s)
            body.pos = vp.vector(
                float(vectors['x'][0]) * AU_TO_METERS,
                float(vectors['y'][0]) * AU_TO_METERS,
                float(vectors['z'][0]) * AU_TO_METERS
            )
            body.vel = vp.vector(
                float(vectors['vx'][0]) * AU_TO_METERS / DAYS_TO_SECONDS,
                float(vectors['vy'][0]) * AU_TO_METERS / DAYS_TO_SECONDS,
                float(vectors['vz'][0]) * AU_TO_METERS / DAYS_TO_SECONDS
            )

            if hasattr(body.sphere, 'clear_trail'):
                body.sphere.clear_trail()

            print(f"Updated: {body.name}")
        except Exception as e:
            print(f"Error fetching data for {body.name}: {e}")


def calculate_accelerations(positions: List[vp.vector], bodies: List[CelestialBody]) -> List[vp.vector]:
    """Calculates gravitational accelerations for each body."""
    accels = []
    for i, _ in enumerate(bodies):
        accel = vp.vector(0, 0, 0)
        for j, other in enumerate(bodies):
            if i != j:
                r_vec = positions[j] - positions[i]
                dist_sq = vp.mag(r_vec) ** 2
                if dist_sq > 0:
                    accel += (other.mu / dist_sq) * vp.norm(r_vec)
        accels.append(accel)
    return accels


def perform_rk4_step(bodies: List[CelestialBody], dt: float) -> None:
    """Performs a single integration step using the 4th-order Runge-Kutta method."""
    positions = [body.pos for body in bodies]
    velocities = [body.vel for body in bodies]
    num_bodies = len(bodies)

    # Step 1
    a1 = calculate_accelerations(positions, bodies)
    v1 = velocities

    # Step 2
    pos2 = [positions[i] + v1[i] * (dt / 2) for i in range(num_bodies)]
    a2 = calculate_accelerations(pos2, bodies)
    v2 = [velocities[i] + a1[i] * (dt / 2) for i in range(num_bodies)]

    # Step 3
    pos3 = [positions[i] + v2[i] * (dt / 2) for i in range(num_bodies)]
    a3 = calculate_accelerations(pos3, bodies)
    v3 = [velocities[i] + a2[i] * (dt / 2) for i in range(num_bodies)]

    # Step 4
    pos4 = [positions[i] + v3[i] * dt for i in range(num_bodies)]
    a4 = calculate_accelerations(pos4, bodies)
    v4 = [velocities[i] + a3[i] * dt for i in range(num_bodies)]

    # Final state update of the objects
    for i, body in enumerate(bodies):
        body.pos = positions[i] + (v1[i] + 2 * v2[i] + 2 * v3[i] + v4[i]) * (dt / 6)
        body.vel = velocities[i] + (a1[i] + 2 * a2[i] + 2 * a3[i] + a4[i]) * (dt / 6)


def get_body_by_name(bodies: List[CelestialBody], name: str) -> Optional[CelestialBody]:
    """Returns a celestial body based on its name."""
    return next((body for body in bodies if body.name == name), None)


def main() -> None:
    bodies = setup_solar_system()
    earth = get_body_by_name(bodies, "Earth")
    atlas = get_body_by_name(bodies, "3I/ATLAS")

    target_date_str = '2025-07-01'
    update_positions_from_date(bodies, target_date_str)

    current_sim_time = datetime.strptime(target_date_str, '%Y-%m-%d')
    step_counter = 0

    print("Simulation started (RK4 Model).")
    print("Press Ctrl+C in the terminal to stop and save the CSV file.")

    # Safe file handling
    try:
        with open('atlas_simulated_trajectory_rk4.csv', mode='w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Date', 'X', 'Y', 'Z'])

            while True:
                vp.rate(1000)
                perform_rk4_step(bodies, TIME_STEP_SECONDS)

                if earth:
                    vp.scene.center = earth.pos

                current_sim_time += timedelta(seconds=TIME_STEP_SECONDS)
                step_counter += 1

                if atlas and step_counter % STEPS_PER_SAVE == 0:
                    csv_writer.writerow([
                        current_sim_time.strftime('%Y-%m-%d %H:%M:%S'),
                        atlas.pos.x, atlas.pos.y, atlas.pos.z
                    ])
                    csv_file.flush()

    except KeyboardInterrupt:
        print("\nSimulation interrupted. CSV file saved and closed.")

if __name__ == "__main__":
    main()
