#!/usr/bin/env python

import sys
import rospy
import actionlib
from os.path import dirname, realpath
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal, MoveBaseActionFeedback
from armor_api.armor_client import ArmorClient
from std_msgs.msg import String
from actionlib_msgs.msg import GoalID
        
        
robot = ''
is_going_to = ''
is_in = ""
client = None
action_client = None

def get_location(data):
    global is_in
    position = data.feedback.base_position.pose.position
    
    if position.x <= -5 and position.y <= 1.25 and is_in != "bathroom1":
        is_in = "bathroom1"
    elif position.x >= 4.75 and position.y <= -0.15 and is_in != "bathroom2":
        is_in = "bathroom2"
    elif position.x <= -5 and position.y >= 1.25 and is_in != "bedroom1":
        is_in = "bedroom1"
    elif position.x <= 2.20 and position.x >= 0 and position.y >= 2.28 and is_in != "bedroom2":
        is_in = "bedroom2"
    elif position.x <= 2.20 and position.x >= 0 and position.y <= 2.28 and position.y >= -0.15 and is_in != "corridor":
        is_in = "corridor"
    elif position.x >= 2.22 and position.y >= -0.15 and is_in != "kitchen":
        is_in = "kitchen"
    elif position.x >= -5 and position.x <= 0 and position.y >= -0.15 and is_in != "living_room":
        is_in = "living_room"

        
def move_robot_to_kitchen():
    move_robot(3.41, 0.95)

def move_robot_to_living_room():
    move_robot(-3.50, 4.00)

def move_robot_to_bathroom1():
    move_robot(-6.13, 0.25)

def move_robot_to_bathroom2():
    move_robot(6, -1)

def move_robot_to_bedroom1():
    move_robot(-6.30, 3.0)

def move_robot_to_bedroom2():
    move_robot(1.45, 4.63)
    
def move_to_room(room):
    rospy.loginfo("[RDST] Received request for " + robot + " to move to " + room)
    if room   == 'kitchen'     : move_robot_to_kitchen()
    elif room == 'living_room' : move_robot_to_living_room()
    elif room == 'bathroom1'   : move_robot_to_bathroom1()
    elif room == 'bathroom2'   : move_robot_to_bathroom2()
    elif room == 'bedroom1'    : move_robot_to_bedroom1()
    elif room == 'bedroom2'    : move_robot_to_bedroom2()
    else: return
    client.manipulation.replace_one_objectprop_b2_ind('isGoingTo', robot, room)
    

def move_robot(x, y):
    action_client.wait_for_server()

    goal = MoveBaseGoal()
    goal.target_pose.header.frame_id = robot + "_tf/map"
    goal.target_pose.header.stamp = rospy.Time.now()
    goal.target_pose.pose.position.x = x
    goal.target_pose.pose.position.y = y
    goal.target_pose.pose.orientation.w = 1.0

    action_client.send_goal(goal)
    rospy.loginfo("[RDST] Request sento to move_base for " + robot + ".")
    
def move_to_location(data):
    move_to_room(data.data)
    

if __name__ == '__main__':
    if len(sys.argv) < 2: robot = 'robot1'
    else: robot = sys.argv[1] 
    
    rospy.init_node('movebase_client_py')
    rospy.Subscriber("destination", String, move_to_location, queue_size=1)
    rospy.Subscriber("move_base/feedback", MoveBaseActionFeedback, get_location, queue_size=1)
    action_client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
    
    # INITIALIZE REFERENCE

    path = dirname(realpath(__file__))
    path = path + "/../ontology/"
    
    client = ArmorClient(robot, robot + "_reference")
    client.utils.load_ref_from_file(path + "robot-ontology.owl", "http://github.com/EmaroLab/robot-ontology",
                                    False, "PELLET", True, True)  # initializing with unbuffered manipulation and buffered reasoning, auto-mounting
    #client.utils.set_log_to_terminal(True)
    client.manipulation.add_ind_to_class(robot, "Robot")
    if robot == "robot1": 
        client.manipulation.add_objectprop_to_ind("isIn", robot, "bathroom1")
        is_in = "bathroom1"
    else: 
        client.manipulation.add_objectprop_to_ind("isIn", robot, "bedroom2")
        is_in = "bedroom2"
    client.utils.sync_buffered_reasoner()
    
    # LOOPING
    
    rospy.loginfo("[RDST] Ready to accept commands on " + robot + "/destination .")
    rospy.loginfo('[RDST] Allowed values are "kitchen", "living_room", "bathroom1", "bathroom2", "bedroom1" and "bedroom2".' )

    r = rospy.Rate(1) # 1hz
    
    while not rospy.is_shutdown():
        try:
            positions = client.query.objectprop_b2_ind("isIn", robot)
            if len(positions) > 0 and is_in != positions[0]:
                rospy.logerr(robot + " moving from " + positions[0] + " and entering " + is_in)
                client.manipulation.replace_objectprop_b2_ind("isIn", robot, is_in, positions[0])
                client.utils.sync_buffered_reasoner()
            
            goals = client.query.objectprop_b2_ind('isGoingTo', robot)
            if len(goals) > 0 and is_going_to != goals[0]:
                rospy.logerr(robot + " is going to " + goals[0])
                is_going_to = goals[0]
                move_to_room(goals[0])
                client.utils.sync_buffered_reasoner()
        except Exception:
            pass
        r.sleep()
        
