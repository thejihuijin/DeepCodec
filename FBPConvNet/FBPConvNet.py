import numpy as np
import matplotlib

from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F
import torch
import torchvision
import torchvision.transforms as transforms
import torch.optim as optim

import os
import datetime
import time

class FBPConvNet(nn.Module):
    def __init__(self):
        super(FBPConvNet, self).__init__()
        # First level, assumed 256x256
        self.conv1_1 = nn.Conv2d(1,64,3,padding=1)
        self.conv1_2 = nn.Conv2d(64,64,3,padding=1)
        self.batch1 = nn.BatchNorm2d(64)

        # Second level, assumed 64 channels of 128x128
        self.conv2_1 = nn.Conv2d(64,128,3,padding=1)
        self.conv2_2 = nn.Conv2d(128,128,3,padding=1)
        self.batch2 = nn.BatchNorm2d(128)
        
        # Third level, assumed 128 channels of 64 x 64 input
        self.conv3_1 = nn.Conv2d(128,256,3,padding=1)
        self.conv3_2 = nn.Conv2d(256,256,3,padding=1)
        self.batch3 = nn.BatchNorm2d(256)
        
        # Fourth level, assumed 256 channels of 32 x 32 input
        self.conv4_1 = nn.Conv2d(256,512,3,padding=1)
        self.conv4_2 = nn.Conv2d(512,512,3,padding=1)
        self.batch4 = nn.BatchNorm2d(512)
        
        #############################################
        # Fifth level, up-conv to 256 channels of 64 x 64
        self.deconv5 = nn.ConvTranspose2d(512,256,3,padding=1,stride=2,output_padding=1)
        self.conv5_1 = nn.Conv2d(512,256,3,padding=1)
        self.conv5_2 = nn.Conv2d(256,256,3,padding=1)
        
        # Sixth level, up-conv to 128 channels of 128x128
        self.deconv6 = nn.ConvTranspose2d(256, 128, 3, padding=1,stride=2,output_padding=1)
        self.conv6_1 = nn.Conv2d(256,128,3,padding=1)
        self.conv6_2 = nn.Conv2d(128,128,3,padding=1)
        
        # Seventh level, up-conv to 64 channels of 256x256
        self.deconv7 = nn.ConvTranspose2d(128,64,3,padding=1,stride=2,output_padding=1)
        self.conv7_1 = nn.Conv2d(128,64,3,padding=1)
        self.conv7_2 = nn.Conv2d(64,64,3,padding=1)
        
        # Eigth level, 1x1 convolution
        self.conv8 = nn.Conv2d(64,1,1)
        
        self.maxpool = nn.MaxPool2d(2)
        self.elu = nn.ELU()
        
        
    def forward(self,x):
        x1_1 = self.batch1(self.elu(self.conv1_1(x)))
        x1_2 = self.batch1(self.elu(self.conv1_2(x1_1)))
        x1_3 = self.batch1(self.elu(self.conv1_2(x1_2)))
        x1 = self.maxpool(x1_3)
        
        x2_1 = self.batch2(self.elu(self.conv2_1(x1)))
        x2_2 = self.batch2(self.elu(self.conv2_2(x2_1)))
        x2 = self.maxpool(x2_2)
        
        x3_1 = self.batch3(self.elu(self.conv3_1(x2)))
        x3_2 = self.batch3(self.elu(self.conv3_2(x3_1)))
        x3 = self.maxpool(x3_2)
        
        x4_1 = self.batch4(self.elu(self.conv4_1(x3)))
        x4_2 = self.batch4(self.elu(self.conv4_2(x4_1)))

        x5_1 = self.deconv5(x4_2)
        x5_2 = torch.cat((x3_2,x5_1),1)
        x5_3 = self.batch3(self.elu(self.conv5_1(x5_2)))
        x5 = self.batch3(self.elu(self.conv5_2(x5_3)))
        
        x6_1 = self.deconv6(x5)
        x6_2 = torch.cat((x2_2,x6_1),1)
        x6_3 = self.batch2(self.elu(self.conv6_1(x6_2)))
        x6 = self.batch2(self.elu(self.conv6_2(x6_3)))
        
        x7_1 = self.deconv7(x6)
        x7_2 = torch.cat((x1_3,x7_1),1)
        x7_3 = self.batch1(self.elu(self.conv7_1(x7_2)))
        x7 = self.batch1(self.elu(self.conv7_2(x7_3)))
        
        x8 = self.conv8(x7)
        y = x8 + x
        
        return y
