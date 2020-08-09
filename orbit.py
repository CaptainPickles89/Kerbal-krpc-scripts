import time
import krpc
import helpers


"""
This script takes a two-stage rocket and launches into an ~80km orbit. This
script currently assumes the following:
- The first stage uses solid fuel boosters
- The second stage has RCS available
- There's enough fuel available to get into orbit
- The stages are in the following order:
    - Solid boosters
    - Decouple & boost liquid fuel
    - Decouple if out of fuel
    - Activate parachute if less than a given altitude
"""


def launch(connection, vessel, direction, target_altitude):
    """
    Launch a given vessel into orbit at a given target altitude.
    :params connection: A krpc connection
    :params vessel: A vessel object
    :params vessel: The direction of the orbit - "north", "east", "south",
    or "west"
    :params target_altitude: The target apoapsis and periapsis altitude in meters
    """
    # Setup heading, control and throttle
    vessel.auto_pilot.engage()
    vessel.auto_pilot.target_pitch_and_heading(90, helpers.heading[direction])
    vessel.control.throttle = 1
    time.sleep(1)

    # Launch
    print("Launch")
    vessel.control.activate_next_stage()

    # Reduce thrusters and set pitch for orbit
    helpers.wait_for_altitude_more_than(connection, vessel, 3000)
    vessel.control.throttle = 0.7
    vessel.auto_pilot.target_pitch = 45

    # Decouple external fuel tanks when empty
    helpers.wait_for_fuel_less_than(connection, vessel, "SolidFuel", 0.1)
    vessel.control.activate_next_stage()

    # Keep boosting until we reach the target orbit altitude
    helpers.wait_for_apoapsis_more_than(connection, vessel, target_altitude)
    vessel.auto_pilot.target_pitch = 0
    vessel.control.throttle = 0
    vessel.control.rcs = True
    time.sleep(1)

    # Keep boosting until the periapsis reaches the target altitude
    while vessel.orbit.periapsis_altitude < target_altitude:
        if vessel.orbit.time_to_apoapsis < 30:
            vessel.control.throttle = 1
        else:
            vessel.control.throttle = 0
    print(f"At target periapsis: {vessel.orbit.periapsis_altitude}")

    # In stable orbit
    vessel.control.rcs = False
    vessel.auto_pilot.disengage()

    # Decouple when out of fuel
    helpers.wait_for_fuel_less_than(connection, vessel, "LiquidFuel", 0.1)
    vessel.auto_pilot.disengage()
    vessel.control.activate_next_stage()

    # Deploy the parachutes when below a certain altitude
    vessel.auto_pilot.sas = False
    deploy_at_altitude = 4000
    helpers.wait_for_altitude_less_than(connection, vessel, deploy_at_altitude)
    vessel.control.activate_next_stage()


if __name__ == "__main__":
    connection = krpc.connect(address="192.168.0.215")
    vessel = connection.space_center.active_vessel
    launch(connection, vessel, "east", 100000)
