#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import torch
import torch.nn as nn
import torch.nn.functional as F

def weights_init(m):
    if isinstance(m, nn.Conv2d):
        nn.init.xavier_uniform_(m.weight)
        try:
            nn.init.constant_(m.bias, 0.01)
        except:
            pass
    if isinstance(m, nn.Linear):
        nn.init.xavier_uniform_(m.weight)
        nn.init.constant_(m.bias, 0.01)

class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.conv1 = nn.Conv2d(1,    64, 5, stride=3, padding=2)
        self.conv2 = nn.Conv2d(64,  128, 5, stride=4, padding=2)
        self.conv3 = nn.Conv2d(128, 256, 3, stride=2, padding=1)
        self.conv4 = nn.Conv2d(256, 256, 3, stride=2, padding=1)
        
        self.bn1 = nn.BatchNorm2d(64)
        self.bn2 = nn.BatchNorm2d(128)
        self.bn3 = nn.BatchNorm2d(256)
        #self.bn4 = nn.BatchNorm2d(256)
        
        self.apply(weights_init)
        self.features = None

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.leaky_relu(x)
        x = F.max_pool2d(x, 2, 2)
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.leaky_relu(x)
        x = F.max_pool2d(x, 2, 2)         
        x = self.conv3(x)
        x = self.bn3(x)
        x = F.leaky_relu(x)
        self.features = x
        x = F.max_pool2d(x, 2, 2)
        x = self.conv4(x)
        #x = self.bn4(x)
        #x = F.leaky_relu(x)
        x = torch.relu(x)
        x = x.view(-1, 256)
        return x
        
class MLP2(nn.Module):
    def __init__(self):
        super(MLP2, self).__init__()
        self.linear1 = nn.Linear(256+1, 512)
        self.linear2 = nn.Linear(512, 512)
        self.linear3 = nn.Linear(512, 511)
        
        self.linear4 = nn.Linear(512, 512)
        self.linear5 = nn.Linear(512, 512)
        self.linear6 = nn.Linear(512, 512)
        
        self.linear7 = nn.Linear(512, 2)
        
        self.apply(weights_init)
        
    def forward(self, x, t):
        x = torch.cat([x, t], dim=1)
        x = self.linear1(x)
        x = F.leaky_relu(x)
        #x = F.dropout(x, p=0.5, training=self.training)
        x = self.linear2(x)
        x = F.leaky_relu(x)
        #x = F.dropout(x, p=0.5, training=self.training)
        x = self.linear3(x)
        x = F.leaky_relu(x)
        #x = F.dropout(x, p=0.5, training=self.training)
        x = torch.cat([x, t], dim=1)
        
        x = self.linear4(x)
        x = F.leaky_relu(x)
        #x = F.dropout(x, p=0.5, training=self.training)
        x = self.linear5(x)
        x = F.leaky_relu(x)
        #x = F.dropout(x, p=0.5, training=self.training)
        x = self.linear6(x)
        x = F.leaky_relu(x)
        #x = F.dropout(x, p=0.5, training=self.training)
        
        x = self.linear7(x)
        
        #x = torch.tanh(x)
        return x
    
class MLP(nn.Module):
    def __init__(self):
        super(MLP, self).__init__()
        self.linear1 = nn.Linear(256+1, 512)
        self.linear2 = nn.Linear(512, 512)
        self.linear3 = nn.Linear(512, 512)
        self.linear4 = nn.Linear(512, 512)
        self.linear5 = nn.Linear(512, 2)
        
        self.apply(weights_init)
        
    def forward(self, x, t):
        x = torch.cat([x, t], dim=1)
        x = self.linear1(x)
        x = F.leaky_relu(x)
        #x = F.dropout(x, p=0.5, training=self.training)
        x = self.linear2(x)
        x = F.leaky_relu(x)
        #x = F.dropout(x, p=0.5, training=self.training)
        x = self.linear3(x)
        x = F.leaky_relu(x)
        #x = F.dropout(x, p=0.5, training=self.training)
        
        x = self.linear4(x)
        x = F.leaky_relu(x)
        #x = F.dropout(x, p=0.5, training=self.training)
        x = self.linear5(x)
        x = torch.tanh(x)
        return x
    
class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.cnn = CNN()
        self.mlp = MLP2()
    
    def forward(self, x, t):
        x = self.cnn(x)
        x = self.mlp(x, t)
        return x
        