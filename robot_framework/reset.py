"""This module handles resetting the state of the computer so the robot can work with a clean slate."""

import shutil

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from robot_framework import config
from robot_framework.sub_process.letters import kill_libreoffice


def reset(orchestrator_connection: OrchestratorConnection) -> None:
    """Clean up, close/kill all programs and start them again. """
    orchestrator_connection.log_trace("Resetting.")
    clean_up(orchestrator_connection)
    close_all(orchestrator_connection)
    kill_all(orchestrator_connection)
    open_all(orchestrator_connection)


def clean_up(orchestrator_connection: OrchestratorConnection) -> None:
    """Do any cleanup needed to leave a blank slate."""
    orchestrator_connection.log_trace("Doing cleanup.")
    shutil.rmtree(config.TMP_DIR, ignore_errors=True)


def close_all(orchestrator_connection: OrchestratorConnection) -> None:
    """Gracefully close all applications used by the robot."""
    orchestrator_connection.log_trace("Closing all applications.")


def kill_all(orchestrator_connection: OrchestratorConnection) -> None:
    """Forcefully close all applications used by the robot."""
    orchestrator_connection.log_trace("Killing all applications.")
    kill_libreoffice()


def open_all(orchestrator_connection: OrchestratorConnection) -> None:
    """Open all programs used by the robot."""
    orchestrator_connection.log_trace("Opening all applications.")
