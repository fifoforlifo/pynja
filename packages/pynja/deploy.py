import os
from . import build

class DeployProject(build.Project):
    def __init__(self, projectMan, variant):
        super().__init__(projectMan, variant)
        self._deployed = False

    def deploy(self, destDir):
        if self._deployed:
            raise Exception("deploy may only be called once per project")
        self.projectMan.deploy(self._runtimeDeps, destDir)
