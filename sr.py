from motor import setpower, readpower

from vis import *
from pwm import *
import logging

vision = vispoll()
vision.next()

from poll import And, Or
from jointio import io
from addhack import add_coroutine
from trampoline import coroutine
from time_event import timeout, TimePoll


