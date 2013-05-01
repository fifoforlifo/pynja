import os
import pynja
import repo

@pynja.project
class java2(repo.JavaProject):
    def emit(self):
        java1 = self.projectMan.get_project("java1", self.variant)

        sources = [
            "com/java2/Runner.java",
        ]

        with self.java_compile(sources) as javac_task:
            javac_task.workingDir = os.path.join(self.projectDir, "source")
            javac_task.classPaths.append(java1.outputPath)

        with self.jar_create("java2.jar") as task:
            task.extraDeps.append(javac_task.outputPath)
