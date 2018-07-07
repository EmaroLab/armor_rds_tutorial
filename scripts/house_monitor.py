#!/usr/bin/env python

import sys
import rospy
import actionlib
from os.path import dirname, realpath
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from armor_api.armor_client import ArmorClient
from std_msgs.msg import String
from actionlib_msgs.msg import GoalID
        
        
## Modify the ontology so that the living does not trigger the event
## Send one robot to the living when one event is triggered
## When living is reached, send the robt back to its original destination
        
client = None
robot1_client = None
robot2_client = None
action_client = None  ## We only need one, as we will always give priority to robot
        
def initialize_refs():
    global client
    global robot1_client
    global robot2_client

    path = dirname(realpath(__file__))
    path = path + "/../ontology/"
    
    client = ArmorClient("house", "house_reference")
    
    client.utils.load_ref_from_file(path + "global-ontology.owl", "http://github.com/EmaroLab/global-ontology",
                                    False, "PELLET", True, True)  # initializing with unbuffered manipulation and buffere reasoning, auto-mounting
    client.utils.set_log_to_terminal(True)
    
    robot1_client = ArmorClient("robot1", "robot1_reference")
    robot1_client.utils.load_ref_from_file(path + "robot-ontology.owl", "http://github.com/EmaroLab/robot-ontology",
                                    False, "PELLET", True, True)  # initializing with unbuffered manipulation and buffere reasoning, auto-mounting
    robot1_client.utils.set_log_to_terminal(True)
    
    robot2_client = ArmorClient("robot2", "robot2_reference")
    robot2_client.utils.load_ref_from_file(path + "robot-ontology.owl", "http://github.com/EmaroLab/robot-ontology",
                                    False, "PELLET", True, True)  # initializing with unbuffered manipulation and buffere reasoning, auto-mounting
    robot2_client.utils.set_log_to_terminal(True)
        
def update_home_kb():
    query = robot1_client.query.objectprop_b2_ind('isIn', "robot1")
    if len(query) > 0: client.manipulation.replace_one_objectprop_b2_ind('isIn', "robot1", query[0])
    query = robot2_client.query.objectprop_b2_ind('isIn', "robot2")
    if len(query) > 0: client.manipulation.replace_one_objectprop_b2_ind('isIn', "robot2", query[0])
    
    query = robot1_client.query.objectprop_b2_ind('isGoingTo', "robot1")
    if len(query) > 0: client.manipulation.replace_one_objectprop_b2_ind('isGoingTo', "robot1", query[0])
    query = robot2_client.query.objectprop_b2_ind('isGoingTo', "robot2")
    if len(query) > 0: client.manipulation.replace_one_objectprop_b2_ind('isGoingTo', "robot2", query[0])
    client.utils.sync_buffered_reasoner()
    

if __name__ == '__main__':
    if len(sys.argv) < 2: robot = ''
    else: robot = sys.argv[1] 
    
    rospy.init_node('movebase_client_py')
    action_client = actionlib.SimpleActionClient('/robot2/move_base', MoveBaseAction)
    rospy.sleep(3) ## wait the sub-references are instantiated first
    
    initialize_refs()
    
    # LOOPING
    rospy.loginfo('[RDST] The smart house starts monitoring the environment!' )

    r = rospy.Rate(1) #1Hz
    
    while not rospy.is_shutdown():
        try:
            update_home_kb()
            
            triggered_events = client.query.ind_b2_class("Triggered")
            
            if len(triggered_events) > 0:
                rospy.logerr("An event has been triggered!")
                robot2_client.manipulation.replace_one_objectprop_b2_ind('isGoingTo', "robot2", "living_room")
                client.manipulation.replace_one_objectprop_b2_ind('isGoingTo', "robot2", "living_room")
                client.manipulation.remove_ind_from_class("crowdedRoomEvent-001", "Triggered")
                client.utils.sync_buffered_reasoner()
                robot2_client.utils.sync_buffered_reasoner()
                
                while robot2_client.query.objectprop_b2_ind("isIn", "robot2")[0] != "living_room":
                    r.sleep() ## wait to reach backup location
            
        except Exception:
            pass
        r.sleep()

    