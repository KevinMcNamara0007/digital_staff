import random
from src.utilities.general import agent_roles


class Agent:
    role: str
    background: str
    task: str
    fid: str
    progress: str = ""

    def __init__(self, role, task):
        self.role = role
        self.task = task
        self.background = agent_roles[role]["Background"]
        self.fid = f"{'M' if role == 'Manager' else 'A'}{random.randint(100000, 999999)}"

    def __str__(self):
        return ("Agent Configuration:\n"
                f"\tBackground: {self.background}\n"
                f"\tRole: {self.role}\n"
                f"\tFID: {self.fid}\n"
                f"\tTask: {self.task}\n"
                f"\tProgress: {self.progress}")
