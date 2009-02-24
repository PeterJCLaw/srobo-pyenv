from motor import setpower, readpower

from vis import *
from pwm import *
import logging

vision = vispoll()
vision.next()

from jointio import *
from addhack import add_coroutine
from trampoline import coroutine
from events import timeout

