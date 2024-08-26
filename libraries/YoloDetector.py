# -*- coding: utf-8 -*-
"""
Created on Thu Jul 27 09:19:38 2023

@author: monza
"""
from ultralytics import YOLO
import torch

class YoloDetector:
    def __init__(self, model_name):
        self.model = self.load_model(model_name)
        self.classes = self.model.names
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print("Usando dispositivo: ", self.device)
    
    def load_model(self, model_name):
        if model_name:
            # Load a model
            model = YOLO(model_name)
        else:
            model = YOLO("runs\\detect\\train15\\weights\\last.pt")
        return model
    
    def getModel(self):
        return self.model
    
    
    def getModelResults(self, img):
        results = self.model.predict(source=img)
        return results

        