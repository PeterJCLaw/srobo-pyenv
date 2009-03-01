from motor import setpower, readpower, motor

from vis import *
from pwm import *
import logging

from poll import And, Or, TimePoll
from jointio import io
from addhack import add_coroutine
from trampoline import coroutine
from time_event import timeout

from power import setleds, getleds, power, setled, getled, power_switch
from games import GOLF, SQUIRREL

