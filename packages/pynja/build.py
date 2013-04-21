import sys
import os
from . import io
from abc import *


def ninja_esc_path(path):
    return path.replace('$','$$').replace(' ','$ ').replace(':', '$:')

def translate_path_list(ninjaFile, paths, separator = " ", prefix = None):
    if prefix and (len(paths) > 0):
        ninjaFile.write(prefix)
    for path in paths:
        pathEsc = ninja_esc_path(path)
        ninjaFile.write(separator)
        ninjaFile.write(pathEsc)

def translate_extra_deps(ninjaFile, task, needPipe):
    prefix = " |" if needPipe else ""
    translate_path_list(ninjaFile, task.extraDeps, " $\n    ", prefix)

def translate_order_only_deps(ninjaFile, task, needPipe):
    prefix = " ||" if needPipe else ""
    translate_path_list(ninjaFile, task.orderOnlyDeps, " $\n    ", prefix)

def get_loaded_modules(rootDir):
    modules = []
    for name, module in sorted(sys.modules.items()):
        path = getattr(module, "__file__", None)
        if not path:
            continue
        if path.endswith("<frozen>"):
            continue
        if not os.path.isabs(path):
            path = os.path.join(rootDir, path)
        modules.append(path)
    return modules


class Variant:
    def __init__(self, string, fieldDefs):
        self.str = string
        parts = self.str.split("-")
        for i in range(len(parts)):
            fieldValue   = parts[i]
            fieldName    = fieldDefs[i * 2 + 0]
            fieldOptions = fieldDefs[i * 2 + 1]
            if fieldName == "str":
                raise Exception("You may not call a variant field 'str'.  Anything else is fine.")
            if not (fieldValue in fieldOptions):
                errstr = "%s is not valid for field %s\n" % (fieldValue, fieldName)
                errstr = errstr + "Valid options are:\n"
                for option in fieldOptions:
                    errstr = errstr + ("    %s\n" % (option,))
                raise Exception(errstr)
            setattr(self, fieldName, fieldValue)

    def __lt__(self, other):
        return self.str < other.str



class BuildTask(metaclass = ABCMeta):
    def __init__(self, project):
        self.project = project
        self.extraDeps = []
        self.extraOutputs = []
        self.orderOnlyDeps = []
        self.phonyTarget = None # name of phony target to declare with this
        self._emitted = False

    def __enter__(self):
        if self._emitted:
            raise Exception("A task should not be re-used in a with statement.")
        return self

    def __exit__(self, type, value, traceback):
        self._emit_once()

    def _emit_once(self):
        if not self._emitted:
            self._emitted = True
            self.emit()

    @abstractmethod
    def emit(self):
        pass


class BuildTasks:
    def __init__(self, tasks):
        self.__dict__["_tasks"] = tasks
        self.__dict__["_emitted"] = False

    def __len__(self):
        return self._tasks.__len__()

    def __getitem__(self, index):
        return self._tasks[index]

    def __iter__(self):
        return self._tasks.__iter__()

    def __setattr__(self, name, value):
        for task in self._tasks:
            setattr(task, name, value)

    def __enter__(self):
        if self._emitted:
            raise Exception("Tasks should not be re-used in a with statement.")
        return self

    def __exit__(self, type, value, traceback):
        self._emit_once()

    def _emit_once(self):
        if not self._emitted:
            self.__dict__["_emitted"] = True
            for task in self._tasks:
                task._emit_once()


class Project(metaclass = ABCMeta):
    def __init__(self, projectMan, variant):
        self.projectMan = projectMan
        self.variant = variant
        self.projectDir = self.get_project_dir()
        self.builtDir = self.get_built_dir()
        self.makeFiles = []

    @abstractmethod
    def get_project_dir(self):
        pass

    @abstractmethod
    def get_built_dir(self):
        pass

    @abstractmethod
    def emit(self):
        pass

    def get_abs_path(self, path):
        if os.path.isabs(path):
            return path
        else:
            return os.path.join(self.projectDir, path)

    def custom_command(self, command, desc = None, inputs = [], outputs = []):
        self.projectMan.emit_custom_command(command, desc, inputs, outputs)

    def copy(self, orig, dest, phonyTarget = None):
        origPath = self.get_abs_path(orig)
        destPath = self.get_abs_path(dest)
        self.projectMan.emit_copy(origPath, destPath, phonyTarget)


class ToolChain(metaclass = ABCMeta):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def emit_rules(self, file):
        pass


class ProjectMan:
    def __init__(self, ninjaFile, ninjaPath):
        self.ninjaFile = ninjaFile
        self.ninjaPath = ninjaPath
        self.ninjaPathEsc = ninja_esc_path(ninjaPath)
        self._projects = {}
        self._toolchains = {}
        self._phonyTargets = {}
        self.emitVS2008Projects = (os.name == 'nt')
        self.emitVS2010Projects = (os.name == 'nt')

    def get_project(self, projName, variantName):
        variants = self._projects.get(projName)
        if variants == None:
            variants = {}
            self._projects[projName] = variants
        project = variants.get(variantName)
        if project == None:
            project = projectFactory[projName](self, variantName)
            variants[variantName] = project
            project.emit()
        return project

    def add_toolchain(self, toolchain):
        if self._toolchains.get(toolchain.name):
            raise NameError("toolchain %s already defined" % toolchain.name)
        self._toolchains[toolchain.name] = toolchain

    def get_toolchain(self, toolchainName):
        return self._toolchains.get(toolchainName)

    def add_phony_target(self, name, path):
        refs = self._phonyTargets.get(name)
        if refs == None:
            refs = []
            self._phonyTargets[name] = refs
        refs.append(path)

    def emit_rules(self):
        ninjaFile = self.ninjaFile
        ninjaFile.write("#############################################\n")
        ninjaFile.write("# CUSTOM_COMMAND\n")
        ninjaFile.write("\n")
        ninjaFile.write("rule CUSTOM_COMMAND\n")
        ninjaFile.write("  command = $COMMAND\n")
        ninjaFile.write("  description = $DESC\n")
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")

        copyCommand = os.path.join(os.path.dirname(__file__), "scripts", "copy-file.py")

        ninjaFile.write("#############################################\n")
        ninjaFile.write("# File copy\n")
        ninjaFile.write("rule FILE_COPY\n")
        ninjaFile.write("  command = python %s \"$in\" \"$out\" \n" % copyCommand)
        ninjaFile.write("  description = Copy $in -> $out.\n")
        ninjaFile.write("\n")
        ninjaFile.write("\n")

        for toolchainName, toolchain in sorted(self._toolchains.items()):
            toolchain.emit_rules(self.ninjaFile)

    def emit_custom_command(self, command, desc = None, inputs = [], outputs = []):
        ninjaFile.write("build $\n")
        for output in outputs:
            outputEsc = ninja_esc_path(output)
            ninjaFile.write("    %s$\n" % outputEsc)
        ninjaFile.write("  : CUSTOM_COMMAND")
        for input in inputs:
            inputEsc = ninjaFile(input)
            ninjaFile.write(" $\n    %s" % inputEsc)
        ninjaFile.write("\n")

        ninjaFile.write("  COMMAND = %s\n" % command)
        ninjaFile.write("  DESC = %s\n" % desc)

    def emit_copy(self, origPath, destPath, phonyTarget = None):
        ninjaFile = self.ninjaFile
        origPathEsc = ninja_esc_path(origPath)
        destPathEsc = ninja_esc_path(destPath)

        ninjaFile.write("build %s : FILE_COPY %s\n" % (destPathEsc, origPathEsc))
        if phonyTarget:
            self.add_phony_target(phonyTarget, destPath)

    def emit_phony_targets(self):
        ninjaFile = self.ninjaFile
        ninjaFile.write("#############################################\n")
        ninjaFile.write("# phony targets\n")
        ninjaFile.write("\n")
        for name, targets in sorted(self._phonyTargets.items()):
            nameEsc = ninja_esc_path(name)
            ninjaFile.write("build %s : phony" % nameEsc)
            for target in targets:
                targetEsc = ninja_esc_path(target)
                ninjaFile.write(" ");
                ninjaFile.write(targetEsc)
            ninjaFile.write("\n")
        ninjaFile.write("\n")

    def get_project_list(self):
        projects = []
        for projName, variants in sorted(self._projects.items()):
            for variant, project in sorted(variants.items()):
                projects.append(project)
        return projects

    def emit_regenerator_target(self, remakeScriptPath):
        ninjaFile = self.ninjaFile
        ninjaPath = self.ninjaPath
        ninjaPathEsc = ninja_esc_path(ninjaPath)
        remakeScriptPathEsc = ninja_esc_path(remakeScriptPath)
        projects = self.get_project_list()
        rootDir = os.path.dirname(remakeScriptPath)

        ninjaFile.write("#############################################\n");
        ninjaFile.write("# Remake build.ninja if any python sources changed.\n");
        ninjaFile.write("rule RERUN_MAKE\n");
        ninjaFile.write("  command = python \"%s\"\n" % remakeScriptPath);
        ninjaFile.write("  description = Running remake script.\n");
        ninjaFile.write("  generator = 1\n");
        ninjaFile.write("  restat = 1\n");
        ninjaFile.write("\n");

        ninjaFile.write("build %s $\n" % ninjaPathEsc)
        for project in projects:
            for path in project.makeFiles:
                pathEsc = ninja_esc_path(path)
                ninjaFile.write("    %s $\n" % pathEsc)
        ninjaFile.write("  : RERUN_MAKE |$\n")
        loadedModules = get_loaded_modules(rootDir)
        for path in sorted(loadedModules):
            pathEsc = ninja_esc_path(path)
            ninjaFile.write("    %s $\n" % pathEsc)
        ninjaFile.write("    %s\n" % remakeScriptPathEsc)
        ninjaFile.write("\n");
        ninjaFile.write("\n");


projectFactory = {}

def project(projectType):
    projectFactory[projectType.__name__] = projectType
    return projectType
