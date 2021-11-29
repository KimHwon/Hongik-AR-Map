import requests, cv2
import pickle, copyreg
import sys

from Server.Config import DATABASE

copyreg.pickle(cv2.KeyPoint().__class__, lambda p: (cv2.KeyPoint, (*p.pt, p.size, p.angle, p.response, p.octave, p.class_id)))


res = requests.get(DATABASE)
res.raise_for_status()
database = pickle.loads(res.content)