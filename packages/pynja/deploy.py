import os
from . import build

class DeployProject(build.Project):
    def __init__(self, projectMan, variant):
        super().__init__(projectMan, variant)
        self._deployed = False

    def deploy(self, destDir, phonyTarget = None):
        if self._deployed:
            raise Exception("deploy may only be called once per project")
        if not phonyTarget:
            phonyTarget = type(self).__name__
        self.projectMan.deploy(self._runtimeDeps, destDir, phonyTarget)
