from __future__ import print_function
import os
import warnings
warnings.filterwarnings('ignore')
from tensorboardX import SummaryWriter
import time
import torch
import shutil
import argparse
from m2det import build_net
import torch.utils.data as data
import torch.backends.cudnn as cudnn
from layers.functions import PriorBox
from data import detection_collate
from configs.CC import Config
from utils.core import *

args = []
config = 'configs/m2det512_resnet101.py'
dataset_prefix = 'VOC'
ngpu = 2
# resume_net = 'weights_train01/Final_M2Det_VOC_size704_netresnet101.pth'
resume_epoch = 0
tensorboard = True
writer = SummaryWriter('runs/train03')

print_info('----------------------------------------------------------------------\n'
           '|                       M2Det Training Program                       |\n'
           '----------------------------------------------------------------------',['yellow','bold'])

logger = set_logger(tensorboard)
global cfg
cfg = Config.fromfile(config)
net = build_net('train', 
                size = cfg.model.input_size, # Only 320, 512, 704 and 800 are supported
                config = cfg.model.m2det_config)
# init_net(net, cfg, resume_net) # init the network with pretrained weights or resumed weights

if ngpu>1:
    net = torch.nn.DataParallel(net)
if cfg.train_cfg.cuda:
    net.cuda()
    cudnn.benchmark = True

optimizer = set_optimizer(net, cfg)
criterion = set_criterion(cfg)
priorbox = PriorBox(anchors(cfg))

with torch.no_grad():
    priors = priorbox.forward()
    if cfg.train_cfg.cuda:
        priors = priors.cuda()


net.train()
epoch = resume_epoch
print_info('===> Loading Dataset...',['yellow','bold'])
dataset = get_dataloader(cfg, dataset_prefix, 'train_sets')
epoch_size = len(dataset) // (cfg.train_cfg.per_batch_size * ngpu)
max_iter = cfg.train_cfg.step_lr[dataset_prefix][-1] * epoch_size
stepvalues = [_*epoch_size for _ in cfg.train_cfg.step_lr[dataset_prefix][:-1]]
print_info('===> Training M2Det on ' + dataset_prefix, ['yellow','bold'])
step_index = 0
if resume_epoch > 0:
    start_iter = resume_epoch * epoch_size
else:
    start_iter = 0
for iteration in range(start_iter, max_iter):
    if iteration % epoch_size == 0:
        batch_iterator = iter(data.DataLoader(dataset, 
                                              cfg.train_cfg.per_batch_size * ngpu, 
                                              shuffle=True, 
                                              num_workers=cfg.train_cfg.num_workers, 
                                              collate_fn=detection_collate))
        if epoch % cfg.model.save_eposhs == 0:
            save_checkpoint(net, cfg, final=False, datasetname = dataset_prefix, epoch=epoch)
        epoch += 1
    load_t0 = time.time()
    if iteration in stepvalues:
        step_index += 1
    lr = adjust_learning_rate(optimizer, cfg.train_cfg.gamma, epoch, step_index, iteration, epoch_size, cfg)
    images, targets = next(batch_iterator)
    if cfg.train_cfg.cuda:
        images = images.cuda()
        targets = [anno.cuda() for anno in targets]
    out = net(images)
    optimizer.zero_grad()
    loss_l, loss_c = criterion(out, priors, targets)
    loss = loss_l + loss_c
#     write_logger({'loc_loss':loss_l.item(),
#                   'conf_loss':loss_c.item(),
#                   'loss':loss.item()},logger,iteration,status=tensorboard)
    loss.backward()
    optimizer.step()
    load_t1 = time.time()
    print_train_log(iteration, cfg.train_cfg.print_epochs,
                        [time.ctime(),epoch,iteration%epoch_size,epoch_size,iteration,loss_l.item(),loss_c.item(),load_t1-load_t0,lr])
    writer.add_scalar('Loss_L', loss_l, epoch)
    writer.add_scalar('Loss_C', loss_c, epoch)
check_point_path = save_checkpoint(net, cfg, final=True, datasetname=dataset_prefix,epoch=-1)


# In[ ]:


print('done')


# In[ ]:


check_point_path


# In[ ]:




