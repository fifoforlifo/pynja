import os
import pynja
import repo

@pynja.project
class java2(repo.JavaProject):
    def emit(self):
        java1 = self.get_java_project("java1", self.variant)

        sources = [
            "com/java2/Runner.java",
        ]

        with self.java_compile(sources) as task:
            task.workingDir = os.path.join(self.projectDir, "source")

        with self.jar_create("java2.jar") as task:
            pass
