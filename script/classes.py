import paramiko
import logging
from .db import User, async_session
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class SSHConnection:
    def __init__(self, host, port=22, username=None, password=None, key_filepath=None, key_password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_filepath = key_filepath
        self.key_password = key_password
        self.client = None
        self.transport = None

    def _connect_with_password(self):
        self.client.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=10
        )

    def _connect_with_key(self):
        pkey = None
        if self.key_filepath:
            key_types = [paramiko.RSAKey, paramiko.DSSKey, paramiko.ECDSAKey, paramiko.Ed25519Key]
            for key_type in key_types:
                try:
                    pkey = key_type.from_private_key_file(self.key_filepath, password=self.key_password)
                    break
                except paramiko.SSHException:
                    continue
            if not pkey:
                raise paramiko.SSHException(f"Unable to load private key: {self.key_filepath}")

        self.client.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            pkey=pkey,
            timeout=10
        )

    def connect(self):
        if self.client and self.client.get_transport() and self.client.get_transport().is_active():
            logger.info(f"Already connected to {self.host}")
            return True

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            logger.info(f"Attempting to connect to {self.host}:{self.port} as {self.username}")
            if self.password:
                logger.info(f"Connecting to {self.host} using password authentication.")
                self._connect_with_password()
            elif self.key_filepath:
                logger.info(f"Connecting to {self.host} using key authentication.")
                self._connect_with_key()
            else:
                raise ValueError(
                    "Password must be provided for authentication as per project requirements (key_filepath is optional).")

            self.transport = self.client.get_transport()
            logger.info(f"Successfully connected to {self.host}")
            return True
        except paramiko.AuthenticationException:
            logger.error(f"Authentication failed for {self.username}@{self.host}")
            self.client = None
            self.transport = None
            raise
        except paramiko.SSHException as e:
            logger.error(f"SSH connection failed for {self.host}: {e}")
            self.client = None
            self.transport = None
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during connection to {self.host}: {e}")
            if self.client:
                self.client.close()
            self.client = None
            self.transport = None
            raise

    def disconnect(self):
        if self.client:
            logger.info(f"Disconnecting from {self.host}")
            self.client.close()
            self.client = None
            self.transport = None
        else:
            logger.info("Not connected, no need to disconnect.")

    def execute_command(self, command):
        if not self.client or not self.transport or not self.transport.is_active():
            logger.error("Cannot execute command: Not connected.")
            raise paramiko.SSHException("Not connected to SSH server. Please connect first.")

        try:
            logger.info(f"Executing command on {self.host}: {command}")
            stdin, stdout, stderr = self.client.exec_command(command, timeout=15)
            exit_status = stdout.channel.recv_exit_status()

            stdout_data = stdout.read().decode('utf-8', errors='replace').strip()
            stderr_data = stderr.read().decode('utf-8', errors='replace').strip()

            logger.debug(f"Command '{command}' exit_status: {exit_status}")
            logger.debug(f"Command '{command}' STDOUT: {stdout_data}")
            logger.debug(f"Command '{command}' STDERR: {stderr_data}")

            return stdout_data, stderr_data, exit_status
        except paramiko.SSHException as e:
            logger.error(f"Failed to execute command '{command}' on {self.host}: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred while executing command '{command}' on {self.host}: {e}")
            raise

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class VMConfigManager:
    def __init__(self, session_maker=async_session):
        self.async_session = session_maker

    async def save_vm_config(self, user_id: int, host: str, port: int, username: str, password: str) -> bool:
        """Saves or updates VM connection parameters for a given user_id."""
        async with self.async_session() as session:
            async with session.begin():
                try:
                    user = await session.get(User, user_id)
                    if not user:
                        logger.error(f"User with ID {user_id} not found. Cannot save VM config.")
                        return False

                    user.vm_host = host
                    user.vm_port = port
                    user.vm_username = username
                    user.vm_password = password

                    session.add(user)
                    await session.commit()
                    logger.info(f"VM configuration saved for user ID {user_id}.")
                    return True
                except SQLAlchemyError as e:
                    await session.rollback()
                    logger.error(f"Database error while saving VM config for user {user_id}: {e}")
                    return False
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Unexpected error while saving VM config for user {user_id}: {e}")
                    return False

    async def get_vm_config(self, user_id: int) -> dict | None:
        """Retrieves VM connection parameters for a given user_id."""
        async with self.async_session() as session:
            try:
                result = await session.execute(select(User).where(User.userid == user_id))
                user = result.scalar_one_or_none()

                if user and user.vm_host and user.vm_username:
                    logger.info(f"VM configuration retrieved for user ID {user_id}.")
                    return {
                        "host": user.vm_host,
                        "port": user.vm_port or 22,
                        "username": user.vm_username,
                        "password": user.vm_password
                    }
                else:
                    logger.warning(f"VM configuration not found or incomplete for user ID {user_id}.")
                    return None
            except SQLAlchemyError as e:
                logger.error(f"Database error while retrieving VM config for user {user_id}: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error while retrieving VM config for user {user_id}: {e}")
                return None