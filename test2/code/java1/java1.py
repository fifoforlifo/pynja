import os
import pynja
import repo

@pynja.project
class java1(repo.JavaProject):
    def emit(self):
        sources = [
            "com/java1/Counter.java",
        ]

        with self.java_compile(sources) as task:
            task.workingDir = os.path.join(self.projectDir, "source")

        with self.jar_create("java1.jar") as task:
            pass
