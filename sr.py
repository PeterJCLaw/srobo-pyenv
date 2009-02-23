from motor import setpower, readpower

from vis import *
from pwm import *
import logging

vision = vispoll()
vision.next()

from jointio import *
