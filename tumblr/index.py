#!/usr/bin/python

import re
from PIL import Image as pil
import os
from random import choice
from math import sqrt as sqr
import util.statistics as stat
import util.measures as measure

idex=re.compile('_(\w{19})_')