moving_rover = {
    "move_forward": "Moving forward at 7km/h",
    "move_backward": "Moving backward at 5km/h",
    "turn_left": "Turning left",
    "stop_turning": "Straightening up",
    "turn_right": "Turning right",
    "stop_moving": "Stopped moving",
    "invalid_control" : "Invalid input: Stopped moving!!"
}

Temp_data = [
    """
    Timestamp,Temperature (°C)
    2025-03-23 08:00,21.5
    2025-03-23 08:05,21.7
    2025-03-23 08:10,22.0
    2025-03-23 08:15,22.4
    2025-03-23 08:20,22.8
    2025-03-23 08:25,23.1
    2025-03-23 08:30,23.5
    2025-03-23 08:35,23.8
    2025-03-23 08:40,24.0
    2025-03-23 08:45,24.3
    2025-03-23 08:50,24.5
    2025-03-23 08:55,24.7
    """,
    """
    Timestamp,Temperature (°C)
    2025-03-23 08:00,-168.5
    2025-03-23 08:05,-168.3
    2025-03-23 08:10,-168.0
    2025-03-23 08:15,-167.6
    2025-03-23 08:20,-167.2
    2025-03-23 08:25,-166.9
    2025-03-23 08:30,-166.5
    2025-03-23 08:35,-166.2
    2025-03-23 08:40,-166.0
    2025-03-23 08:45,-165.7
    2025-03-23 08:50,-165.5
    2025-03-23 08:55,-165.3
    """
]

greetings = {
    "greeting_1": "Hello World!",
    "greeting_2": "Goodbye!",
}

status_response = \
    ["""
    Lunar Rover Status Update
    Mission Time: 13:00 GMT
    Location: Sector A
    Power Status: 42% battery remaining — below optimal threshold
 

    Surface operations impacted by environmental conditions and minor system faults.
    Awaiting engineering review and corrective action on mobility and sensor anomalies.
    """,
     """
     Lunar Rover Status Update
     Mission Time: 12:00 GMT
     Location: Sector B     

     Surface operations are proceeding nominally. No system anomalies detected.
     Continuing with exploration and sample retrieval as planned.
     """
     ]