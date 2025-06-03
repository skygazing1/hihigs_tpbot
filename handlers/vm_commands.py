import logging
import re
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from script.classes import VMConfigManager, SSHConnection
import paramiko

logger = logging.getLogger(__name__)
router = Router()