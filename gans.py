#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 19:11:16 2020

@author: maan
"""


# Deep Convolutional GANs

# Importing the libraries
from __future__ import print_function
import torch
import torch.nn as nn
import torch.nn.parallel
import torch.optim as optim
import torch.utils.data
import torchvision.datasets as dset
import torchvision.transforms as transforms
import torchvision.utils as vutils
from torch.autograd import Variable

# Setting some hyperparameters
batchSize = 64 # We set the size of the batch.
imageSize = 64 # We set the size of the generated images (64x64).

# Creating the transformations
transform = transforms.Compose([transforms.Resize(imageSize), transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),]) # We create a list of transformations (scaling, tensor conversion, normalization) to apply to the input images.

# Loading the dataset
dataset = dset.CIFAR10(root = './data', download = True, transform = transform) # We download the training set in the ./data folder and we apply the previous transformations on each image.
dataloader = torch.utils.data.DataLoader(dataset, batch_size = batchSize, shuffle = True, num_workers = 2) # We use dataLoader to get the images of the training set batch by batch.

# Defining the weights_init function that takes as input a neural network m and that will initialize all its weights.
def weights_init(m):
    classname = m.__class__.__name__
    if classname.find('Conv') != -1:
        m.weight.data.normal_(0.0, 0.02)
    elif classname.find('BatchNorm') != -1:
        m.weight.data.normal_(1.0, 0.02)
        m.bias.data.fill_(0)

# Defining the generator

class G(nn.Module): # We introduce a class to define the generator.

    def __init__(self): 
        super(G, self).__init__() 
        self.main = nn.Sequential( 
            nn.ConvTranspose2d(100, 512, 4, 1, 0, bias = False), 
            nn.BatchNorm2d(512), 
            nn.ReLU(True), 
            nn.ConvTranspose2d(512, 256, 4, 2, 1, bias = False), 
            nn.BatchNorm2d(256),
            nn.ReLU(True), 
            nn.ConvTranspose2d(256, 128, 4, 2, 1, bias = False), 
            nn.BatchNorm2d(128),
            nn.ReLU(True), 
            nn.ConvTranspose2d(128, 64, 4, 2, 1, bias = False), 
            nn.BatchNorm2d(64), 
            nn.ReLU(True),
            nn.ConvTranspose2d(64, 3, 4, 2, 1, bias = False), 
            nn.Tanh()
        )

    def forward(self, input):
        output = self.main(input) 
        return output 

# Creating the generator
netG = G() # We create the generator object.
netG.apply(weights_init) # We initialize all the weights of its neural network.

# Defining the discriminator

class D(nn.Module): # We introduce a class to define the discriminator.

    def __init__(self): 
        super(D, self).__init__() 
        self.main = nn.Sequential( 
            nn.Conv2d(3, 64, 4, 2, 1, bias = False), 
            nn.LeakyReLU(0.2, inplace = True), 
            nn.Conv2d(64, 128, 4, 2, 1, bias = False), 
            nn.BatchNorm2d(128), 
            nn.LeakyReLU(0.2, inplace = True),
            nn.Conv2d(128, 256, 4, 2, 1, bias = False), 
            nn.BatchNorm2d(256), 
            nn.LeakyReLU(0.2, inplace = True), 
            nn.Conv2d(256, 512, 4, 2, 1, bias = False), 
            nn.BatchNorm2d(512), 
            nn.LeakyReLU(0.2, inplace = True),
            nn.Conv2d(512, 1, 4, 1, 0, bias = False), 
            nn.Sigmoid()
        )

    def forward(self, input):
        output = self.main(input) 
        return output.view(-1) 

# Creating the discriminator
netD = D() # We create the discriminator object.
netD.apply(weights_init) # We initialize all the weights of its neural network.

# Training the DCGANs

criterion = nn.BCELoss() # We create a criterion object that will measure the error between the prediction and the target.
optimizerD = optim.Adam(netD.parameters(), lr = 0.0002, betas = (0.5, 0.999)) # We create the optimizer object of the discriminator.
optimizerG = optim.Adam(netG.parameters(), lr = 0.0002, betas = (0.5, 0.999)) # We create the optimizer object of the generator.

for epoch in range(25): # We iterate over 25 epochs.

    for i, data in enumerate(dataloader, 0):
        
        # 1st Step: Updating the weights of the neural network of the discriminator

        netD.zero_grad() 
        
        # Training the discriminator with a real image of the dataset
        real, _ = data 
        input = Variable(real)
        target = Variable(torch.ones(input.size()[0])) 
        output = netD(input) 
        errD_real = criterion(output, target) 
        
        # Training the discriminator with a fake image generated by the generator
        noise = Variable(torch.randn(input.size()[0], 100, 1, 1)) 
        fake = netG(noise) 
        target = Variable(torch.zeros(input.size()[0])) 
        output = netD(fake.detach())
        errD_fake = criterion(output, target) 

        # Backpropagating the total error
        errD = errD_real + errD_fake 
        errD.backward() 
        optimizerD.step() 

        # 2nd Step: Updating the weights of the neural network of the generator

        netG.zero_grad() 
        target = Variable(torch.ones(input.size()[0])) 
        output = netD(fake)
        errG = criterion(output, target) 
        errG.backward() 
        optimizerG.step() 
        
        # 3rd Step: Printing the losses and saving the real images and the generated images of the minibatch every 100 steps

        print('[%d/%d][%d/%d] Loss_D: %.4f Loss_G: %.4f' % (epoch, 25, i, len(dataloader), errD.data, errG.data)) # We print les losses of the discriminator (Loss_D) and the generator (Loss_G).
        if i % 100 == 0: # Every 100 steps:
            vutils.save_image(real, '%s/real_samples.png' % "./results", normalize = True) # We save the real images of the minibatch.
            fake = netG(noise) # We get our fake generated images.
            vutils.save_image(fake.data, '%s/fake_samples_epoch_%03d.png' % ("./results", epoch), normalize = True) # We also save the fake generated images of the minibatch.