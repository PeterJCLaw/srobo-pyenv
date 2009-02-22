from motor import setpower, readpower

from vis import *
from pwm import setpos
import logging

vision = vispoll()
vision.next()

from jointio import *
