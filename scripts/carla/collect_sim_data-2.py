#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from os.path import join, dirname
sys.path.insert(0, join(dirname(__file__), '..'))

import simulator
simulator.load('/home/wang/CARLA_0.9.9.4')
import carla
sys.path.append('/home/wang/CARLA_0.9.9.4/PythonAPI/carla')
from agents.navigation.basic_agent import BasicAgent
from simulator import config, set_weather, add_vehicle
from simulator.sensor_manager import SensorManager
from utils.navigator_sim import get_random_destination, get_map, get_nav, replan2, close2dest

import os
import cv2
import time
import copy
import random
import argparse
import numpy as np
from tqdm import tqdm

global_img = None
global_pcd = None
global_nav = None
global_control = None
global_pos = None
global_acceleration = None
global_angular_velocity = None
global_vel = None
MAX_SPEED = 40

parser = argparse.ArgumentParser(description='Params')
parser.add_argument('-d', '--data', type=int, default=10, help='data index')
parser.add_argument('-n', '--num', type=int, default=50000, help='total number')
args = parser.parse_args()

data_index = args.data
save_path = '/media/wang/DATASET/CARLA/town01/'+str(data_index)+'/'

def mkdir(path):
    os.makedirs(save_path+path, exist_ok=True)

mkdir('')
mkdir('img/')
mkdir('pcd/')
mkdir('nav/')
mkdir('state/')
mkdir('cmd/')
cmd_file = open(save_path+'cmd/cmd.txt', 'w+')
pos_file = open(save_path+'state/pos.txt', 'w+')
vel_file = open(save_path+'state/vel.txt', 'w+')
acc_file = open(save_path+'state/acc.txt', 'w+')
angular_vel_file = open(save_path+'state/angular_vel.txt', 'w+')

def save_data(index):
    global global_img, global_pcd, global_nav, global_control, global_pos, global_vel,global_acceleration, global_angular_velocity
    cv2.imwrite(save_path+'img/'+str(index)+'.png', global_img)
    cv2.imwrite(save_path+'nav/'+str(index)+'.png', global_nav)
    np.save(save_path+'pcd/'+str(index)+'.npy', global_pcd)
    cmd_file.write(index+'\t'+
                   str(global_control.throttle)+'\t'+
                   str(global_control.steer)+'\t'+
                   str(global_control.brake)+'\n')
    pos_file.write(index+'\t'+
                   str(global_pos.location.x)+'\t'+
                   str(global_pos.location.y)+'\t'+
                   str(global_pos.location.z)+'\t'+
                   str(global_pos.rotation.pitch)+'\t'+
                   str(global_pos.rotation.yaw)+'\t'+
                   str(global_pos.rotation.roll)+'\t'+'\n')
    vel_file.write(index+'\t'+
                   str(global_vel.x)+'\t'+
                   str(global_vel.y)+'\t'+
                   str(global_vel.z)+'\t'+'\n')
    acc_file.write(index+'\t'+
                   str(global_acceleration.x)+'\t'+
                   str(global_acceleration.y)+'\t'+
                   str(global_acceleration.z)+'\t'+'\n')
    angular_vel_file.write(index+'\t'+
                   str(global_angular_velocity.x)+'\t'+
                   str(global_angular_velocity.y)+'\t'+
                   str(global_angular_velocity.z)+'\t'+'\n')

def image_callback(data):
    global global_img
    array = np.frombuffer(data.raw_data, dtype=np.dtype("uint8")) 
    array = np.reshape(array, (data.height, data.width, 4)) # RGBA format
    global_img = array
    
def lidar_callback(data):
    global global_pcd
    lidar_data = np.frombuffer(data.raw_data, dtype=np.float32).reshape([-1, 3])
    point_cloud = np.stack([-lidar_data[:,1], -lidar_data[:,0], -lidar_data[:,2]])
    mask = np.where((point_cloud[0] > 1.0)|(point_cloud[0] < -4.0)|(point_cloud[1] > 1.2)|(point_cloud[1] < -1.2))[0]
    point_cloud = point_cloud[:, mask]
    mask = np.where(point_cloud[2] > -1.95)[0]
    point_cloud = point_cloud[:, mask]
    global_pcd = point_cloud
    #world.set_weather(carla.WeatherParameters.ClearNoon)
class World:
    def __init__(self, player, carla_world):
        self.player = player
        self.world = carla_world
    
from agents.navigation.behavior_agent import BehaviorAgent    
def main():
    global global_nav, global_control, global_pos, global_vel, global_acceleration, global_angular_velocity
    client = carla.Client(config['host'], config['port'])
    client.set_timeout(config['timeout'])
    
    #world = client.get_world()
    world = client.load_world('Town01')
    """
    weather = carla.WeatherParameters(
        cloudiness=random.randint(0,80),
        precipitation=0,
        sun_altitude_angle=random.randint(40,90)
    )
    set_weather(world, weather)
    """
    world.set_weather(carla.WeatherParameters.MidRainSunset)
    
    blueprint = world.get_blueprint_library()
    world_map = world.get_map()
    
    vehicle = add_vehicle(world, blueprint, vehicle_type='vehicle.audi.a2')
    # Enables or disables the simulation of physics on this actor.
    vehicle.set_simulate_physics(True)
    _world = World(vehicle, world)
    sensor_dict = {
        'camera':{
            'transform':carla.Transform(carla.Location(x=0.5, y=0.0, z=2.5)),#'transform':carla.Transform(carla.Location(x=-3.0, y=0.0, z=2.5), carla.Rotation(pitch=-20)),
            'callback':image_callback,
            },
        'lidar':{
            'transform':carla.Transform(carla.Location(x=0.5, y=0.0, z=2.5)),
            'callback':lidar_callback,
            },
        }

    sm = SensorManager(world, blueprint, vehicle, sensor_dict)
    sm.init_all()
    time.sleep(0.3)
    
    spawn_points = world_map.get_spawn_points()
    waypoint_tuple_list = world_map.get_topology()
    origin_map = get_map(waypoint_tuple_list)

    #agent = BasicAgent(vehicle, target_speed=MAX_SPEED)
    agent = BehaviorAgent(vehicle, ignore_traffic_light=True, behavior='normal')
    _destination = carla.Transform()
    destination = world.get_random_location_from_navigation()
    _destination.location = destination

    #port = 8000
    #tm = client.get_trafficmanager(port)
    #tm.ignore_lights_percentage(vehicle,100)
    
    #destination = get_random_destination(spawn_points)
    plan_map = replan2(agent, _destination, copy.deepcopy(origin_map))
    #agent.set_destination(agent.vehicle.get_location(), destination, clean=True)
    
    #for cnt in tqdm(range(args.num)):
    for cnt in range(args.num):
        if close2dest(vehicle, _destination):
            _destination = carla.Transform()
            destination = world.get_random_location_from_navigation()
            _destination.location = destination
            plan_map = replan2(agent, _destination, copy.deepcopy(origin_map))
            #agent.set_destination(agent.vehicle.get_location(), destination, clean=True)

        if vehicle.is_at_traffic_light():
            traffic_light = vehicle.get_traffic_light()
            if traffic_light.get_state() == carla.TrafficLightState.Red:
                traffic_light.set_state(carla.TrafficLightState.Green)
            
        agent.update_information(_world)
        
        speed_limit = vehicle.get_speed_limit()
        agent.get_local_planner().set_speed(speed_limit)
        
        control = agent.run_step()
        control.manual_gear_shift = False
        global_control = control
        vehicle.apply_control(control)
        nav = get_nav(vehicle, plan_map)

        global_nav = nav
        global_pos = vehicle.get_transform()
        global_vel = vehicle.get_velocity()
        global_acceleration = vehicle.get_acceleration()
        global_angular_velocity = vehicle.get_angular_velocity()
        
        #yaw = global_pos.rotation.yaw
        #_ax = global_acceleration.x
        #_ay = global_acceleration.y
        #ax = _ax*np.cos(yaw) + _ay*np.sin(yaw)
        #ay = _ay*np.cos(yaw) - _ax*np.sin(yaw)
        
        #cv2.imshow('Nav', nav)
        cv2.imshow('Vision', global_img)
        cv2.waitKey(10)
        index = str(time.time())
        #save_data(index)
        
    cmd_file.close()
    pos_file.close()
    vel_file.close()
    acc_file.close()
    angular_vel_file.close()
    
    cv2.destroyAllWindows()
    sm.close_all()
    vehicle.destroy()
        
if __name__ == '__main__':
    main()