"""File: Tracker.py
Keep track of objects based on observations
"""

import numpy as np 

class Track: 
    """Track object, represents a single object"""
    def __init__(self, pos=None): 
        self.active = True 
        #List of positions all associated with this object
        self.pos_wrt_cam_list = []
        if pos is not None: 
            self.pos_wrt_cam_list.append(np.array(pos))

    @property
    def pos_wrt_cam(self): 
        return np.mean(np.array(self.pos_wrt_cam_list), axis=0)

class Tracker: 
    """Tracker object, takes in positions and associates them with specific tracks"""
    def __init__(self): 
        self.tracks = []

    @property
    def has_active_tracks(self): 
        for track in self.tracks: 
            if track.active: 
                return True
        return False 

    def add_track(self, new_pos, min_dist = 50):
        """Add a track to list of current tracks. 
        If a track already exists close to the one passed in, instead add it to that track.  

        args: 
            new_pos (float, float, float): new position to add to list of existing tracks
            min_dist ()

        NOTE: These tracks are currently in relation to the camera. 
        """ 
        for track in self.tracks: 
            dist = np.linalg.norm(track.pos_wrt_cam - new_pos)
            if dist<min_dist: 
                track.pos_wrt_cam_list.append(new_pos)
                return 
        self.tracks.append(Track(new_pos))
