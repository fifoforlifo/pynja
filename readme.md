# pynja

Avinash Baliga / 2013

pynja is a meta-build system written in Python that produces [Ninja Build files](http://martine.github.com/ninja/).

You get to define a python class for each library or program you want to build, and instantiate it for each
*variant* you wish to build in order to define targets.  Instantiation can occur either from the root level
(for top level targets), or from within another library/program module when there's a dependency.

There are built in abstractions for C/C++ compilation, and it's easy to define custom targets and generators.

Everything is written in regular Python, and you can run any Python code from your own build scripts.
Python also has terrific editing and debugging tools, which means with pynja you can actually develop
and debug your build like the rest of your software.

This software package's first incarnation was [plinja, a Perl -> Ninja meta-build](https://github.com/fifoforlifo/plinja).


## At a glance.

    import pynja
    import upynja


    @pynja.project
    class Prog0(repo.cpp.CppProject):
        def emit(self):
            libA0 = self.projectMan.get_project('A0', self.variant)
            libA1 = self.projectMan.get_project('A1', self.variant)

            # compile one file at a time with per-file settings
            with self.cpp_compile_one("Source/e0_0.cpp") as task:
                task.includePaths.append(repo.rootPaths.A0 + "/IncludeSpecial")
            with self.cpp_compile_one("Source/e0_7.cpp") as task:
                # force no optimizations on this file
                task.optimize = 0

            # compile multiple files at a time
            sources = [
                "Source/e0_6.cpp",
                "Source/e0_1.cpp",
                "Source/e0_2.cpp",
            ]
            with self.cpp_compile(sources) as tasks:
                pass

            # compile multiple files at a time, with same custom per-file settings
            # on each file in the list
            sloppyFiles = [
                "Source/e0_3.cpp",
                "Source/e0_4.cpp",
                "Source/e0_5.cpp",
            ]
            with self.cpp_compile(sloppyFiles) as tasks:
                for task in tasks:
                    task.warnLevel = 1

            sloppyFiles_b = [
                "Source/e0_3b.cpp",
                "Source/e0_4b.cpp",
                "Source/e0_5b.cpp",
            ]
            with self.cpp_compile(sloppyFiles_b) as tasks:
                # broadcast write
                tasks.warnLevel = 1

            # add libraries last
            self.add_input_lib(libA0.libraryPath)
            self.add_input_lib(libA1.libraryPath)

            with self.make_executable("prog0") as task:
                pass

            self.copy(self.outputPath, self.outputPath + ".copy")

        # set c++ compile options that are common to all files in the project
        def set_cpp_compile_options(self, task):
            super().set_cpp_compile_options(task)
            task.includePaths.append(repo.rootPaths.A0 + "/Include")
            task.includePaths.append(repo.rootPaths.A1 + "/Include")


## Guiding principles.

For a meta-build:

-   It must be debuggable.
-   Written in a real programming language.
-   Avoid repetition.
-   No weird assumptions, like a single global toolchain per build.
-   Allow specifying a precise file-level dependency graph.

For a build engine:

-   Incremental builds must be fast.  (ninja - yes!)
-   Full file-level dependency checking.  (ninja - yes!)
-   Implicit dependency checking.  (ninja - yes! - with a dependency generator)
-   Implicit dependency discovery and retry.  (ninja - no - if you have e.g. a generated header, you must define a dependency manually)


## Description of components.

... TODO ...


## Why another build system?

Because the ones out there are *still* not good enough!

... TODO ...

