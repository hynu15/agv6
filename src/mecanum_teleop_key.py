#!/usr/bin/env python3

import rospy
from std_msgs.msg import Float64
import sys, select, os
import tty, termios
from geometry_msgs.msg import Twist

# Key mapping
msg = """
Control Your Mecanum Drive Robot!
---------------------------
Moving around:
   q    w    e
   a    s    d
   z    x    c

w/x : forward/backward
a/d : strafe left/right
q/e : rotate counter-clockwise/clockwise
z/c : diagonal left-forward/right-forward
s : stop

CTRL-C to quit
"""

# Key bindings
moveBindings = {
    'w': (1, 0, 0),    # forward
    'x': (-1, 0, 0),   # backward
    'a': (0, 1, 0),    # strafe left
    'd': (0, -1, 0),   # strafe right
    'q': (0, 0, 1),    # rotate counter-clockwise
    'e': (0, 0, -1),   # rotate clockwise
    'z': (0.7, 0.7, 0),    # diagonal left-forward
    'c': (0.7, -0.7, 0),   # diagonal right-forward
    's': (0, 0, 0),    # stop
}

def getKey():
    """Get keyboard input"""
    tty.setraw(sys.stdin.fileno())
    select.select([sys.stdin], [], [], 0)
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def mecanum_control(x, y, angular_z):
    """Convert x, y, angular_z to wheel velocities
    
    For mecanum wheels:
    front_left = x - y - angular_z
    front_right = x + y + angular_z
    rear_left = x + y - angular_z
    rear_right = x - y + angular_z
    """
    # Scale values for better control
    linear_scale = 5.0
    angular_scale = 2.0
    
    # Calculate wheel velocities
    front_left = (x - y - angular_z) * linear_scale
    front_right = (x + y + angular_z) * linear_scale
    rear_left = (x + y - angular_z) * linear_scale
    rear_right = (x - y + angular_z) * linear_scale
    
    return front_left, front_right, rear_left, rear_right

if __name__ == "__main__":
    settings = termios.tcgetattr(sys.stdin)
    
    rospy.init_node('mecanum_teleop_key')
    
    # Publishers for each wheel
    fl_pub = rospy.Publisher('/agv6/Wheel_left_front_jt_controller/command', Float64, queue_size=1)
    fr_pub = rospy.Publisher('/agv6/Wheel_right_front_jt_controller/command', Float64, queue_size=1)
    rl_pub = rospy.Publisher('/agv6/Wheel_left_rear_jt_controller/command', Float64, queue_size=1)
    rr_pub = rospy.Publisher('/agv6/Wheel_right_rear_jt_controller/command', Float64, queue_size=1)
    
    # Initialize messages
    fl_msg = Float64()
    fr_msg = Float64()
    rl_msg = Float64()
    rr_msg = Float64()
    
    x = 0
    y = 0
    angular_z = 0
    
    try:
        print(msg)
        while not rospy.is_shutdown():
            key = getKey()
            
            # Exit on Ctrl+C
            if key == '\x03':
                break
                
            # Update movement based on key
            if key in moveBindings.keys():
                x = moveBindings[key][0]
                y = moveBindings[key][1]
                angular_z = moveBindings[key][2]
                
                # Calculate wheel speeds
                fl, fr, rl, rr = mecanum_control(x, y, angular_z)
                
                # Set messages
                fl_msg.data = fl
                fr_msg.data = fr
                rl_msg.data = rl
                rr_msg.data = rr
                
                # Publish messages
                fl_pub.publish(fl_msg)
                fr_pub.publish(fr_msg)
                rl_pub.publish(rl_msg)
                rr_pub.publish(rr_msg)
                
                print(f"FL: {fl:.2f}, FR: {fr:.2f}, RL: {rl:.2f}, RR: {rr:.2f}")
            
    except Exception as e:
        print(e)
    
    finally:
        # Stop the robot when exiting
        fl_msg.data = 0
        fr_msg.data = 0
        rl_msg.data = 0
        rr_msg.data = 0
        
        fl_pub.publish(fl_msg)
        fr_pub.publish(fr_msg)
        rl_pub.publish(rl_msg)
        rr_pub.publish(rr_msg)
        
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings) 