from abc import *


class Variant:
    def __init__(self, string, fieldDefs):
        self.str = string
        parts = self.str.split("-")
        for i in range(len(parts)):
            fieldValue   = parts[i]
            fieldName    = fieldDefs[i * 2 + 0]
            fieldOptions = fieldDefs[i * 2 + 1]
            if not (fieldValue in fieldOptions):
                errstr = "%s is not valid for field %s\n" % (fieldValue, fieldName)
                errstr = errstr + "Valid options are:\n"
                for option in fieldOptions:
                    errstr = errstr + ("    %s\n" % (option,))
                raise Exception(errstr)
            setattr(self, fieldName, fieldValue)


class BuildTask(metaclass = ABCMeta):
    def __init__(self, project):
        self.project = project
        self.extraDeps = []
        self.orderOnlyDeps = []
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
        """To be implemented by project author -- contains build commands."""
        pass

    def copy(self, origPath, destPath):
        print(destPath)
        pass



class ToolChain(metaclass = ABCMeta):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def emit_rules(self, file):
        pass


class ProjectMan:
    def __init__(self):
        self._projects = {}
        self._toolchains = {}

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
        return self._toolchains[toolchainName]



projectFactory = {}

def project(projectType):
    projectFactory[projectType.__name__] = projectType
    return projectType
