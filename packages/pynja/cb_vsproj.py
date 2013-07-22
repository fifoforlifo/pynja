import os
import uuid
from . import io
from . import cpp


def _is_source_file(filename):
    return filename.endswith(".c") or filename.endswith(".cpp") or filename.endswith(".cxx")

def _get_project_data(project, ext, codeBrowsingDir):
    projName = type(project).__name__
    vsProjGuid = uuid.uuid5(uuid.NAMESPACE_DNS, project.projectDir)
    vsProjPath = os.path.normpath(os.path.join(codeBrowsingDir, project.projectRelDir, projName + ext))
    return (projName, vsProjGuid, vsProjPath)

def _emit_sln(slnVersion, vsProjList, vsSlnPath, variantNames):
    variantNames = sorted(variantNames)
    vsProjList = sorted(vsProjList, key = lambda vsProjInfo: vsProjInfo[0])
    strings = []
    strings.append("Microsoft Visual Studio Solution File, Format Version %s\n" % (slnVersion))
    for vsProjInfo in vsProjList:
        (projName, vsProjGuid, vsProjPath) = vsProjInfo
        vsProjGuidStr = str(vsProjGuid).upper()
        strings.append(r'''Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "%s", "%s", "{%s}"%s'''
                       % (projName, vsProjPath, vsProjGuidStr, "\n"))
        strings.append("EndProject\n")
    strings.append(r'''Global
	GlobalSection(SolutionConfigurationPlatforms) = preSolution
''')
    strings.append("		%s|Win32 = %s|Win32\n" % ("all", "all"))
    for variantName in variantNames:
        strings.append("		%s|Win32 = %s|Win32\n" % (variantName, variantName))
    strings.append("	EndGlobalSection\n")

    strings.append("	GlobalSection(ProjectConfigurationPlatforms) = postSolution\n")
    for vsProjInfo in vsProjList:
        (projName, vsProjGuid, vsProjPath) = vsProjInfo
        strings.append("		{%s}.%s|Win32.ActiveCfg = %s|Win32\n" % (vsProjGuid, "all", "all"))
        strings.append("		{%s}.%s|Win32.Build.0 = %s|Win32\n" % (vsProjGuid, "all", "all"))
        for variantName in variantNames:
            strings.append("		{%s}.%s|Win32.ActiveCfg = %s|Win32\n" % (vsProjGuid, variantName, variantName))
            strings.append("		{%s}.%s|Win32.Build.0 = %s|Win32\n" % (vsProjGuid, variantName, variantName))
    strings.append("	EndGlobalSection\n")

    strings.append(r'''	GlobalSection(SolutionProperties) = preSolution
		HideSolutionNode = FALSE
	EndGlobalSection
EndGlobal
''')

    vsSlnContents = "".join(strings)
    io.write_file_if_different(vsSlnPath, vsSlnContents)


class VSGenerator:
    def __init__(self):
        self._projectsEmitted = False

    def emit_sln(self, slnName, cbProjectRefs):
        if not self._projectsEmitted:
            self.emit_vs_projects()

        vsProjList = []
        allVariantNames = set()
        for project in cbProjectRefs:
            vsProjInfo = _get_project_data(project, self.projExt, self.codeBrowsingDir)
            vsProjList.append(vsProjInfo)
            variants = self.projectMan._projects[vsProjInfo[0]]
            for variant in variants:
                allVariantNames.add(str(variant))

        slnPath = os.path.join(self.codeBrowsingDir, slnName + self.slnBaseName)
        _emit_sln(self.slnVer, vsProjList, slnPath, allVariantNames)


class VS2008(VSGenerator):
    def __init__(self, projectMan, codeBrowsingDir = None):
        super().__init__()
        self.projectMan = projectMan
        self.slnVer = "10.00"
        self.slnBaseName = "_vs2008.sln"
        self.projExt = ".vcproj"
        if codeBrowsingDir:
            self.codeBrowsingDir = codeBrowsingDir
        else:
            self.codeBrowsingDir = os.path.dirname(projectMan.ninjaPath)

    def _def_config(variantName, ninjaDir, targetName, proj):
        defines = ""
        includePaths = ""
        forceIncludes = ""
        if proj and getattr(proj, "set_cpp_compile_options", None):
            task = cpp.CppTask(proj, "dummy", "dummy.o", proj.projectDir)
            proj.set_cpp_compile_options(task)
            defines = ";".join(task.defines)
            includePaths = ";".join(task.includePaths)
            forceIncludes = task.usePCH if task.usePCH else ""
        config = \
r'''        <Configuration
            Name="{0}|Win32"
            OutputDirectory="$(ConfigurationName)"
            IntermediateDirectory="$(ConfigurationName)"
            ConfigurationType="0"
            >
            <Tool
                Name="VCNMakeTool"
                BuildCommandLine="SET VS_UNICODE_OUTPUT= &#x0D;&#x0A; SET NINJA_STATUS=[%%s/%%t - %%e] &#x0D;&#x0A; cd {1} &#x0D;&#x0A; ninja {2}"
                ReBuildCommandLine="SET VS_UNICODE_OUTPUT= &#x0D;&#x0A; SET NINJA_STATUS=[%%s/%t - %%e] &#x0D;&#x0A; cd {1} &#x0D;&#x0A; ninja -t clean {2} &#x0D;&#x0A; ninja {2}"
                CleanCommandLine="SET VS_UNICODE_OUTPUT= &#x0D;&#x0A; SET NINJA_STATUS=[%%s/%%t - %%e] &#x0D;&#x0A; cd {1} &#x0D;&#x0A; ninja -t clean"
                Output="{6}"
                PreprocessorDefinitions="{3}"
                IncludeSearchPath="{4}"
                ForcedIncludes="{5}"
                AssemblySearchPath=""
                ForcedUsingAssemblies=""
                CompileAsManaged=""
            />
        </Configuration>
'''.format(variantName, ninjaDir, targetName, defines, includePaths, forceIncludes, getattr(proj, "outputPath", "o"))
        return config

    def _def_files(sourceDir, relDir, strings):
        children = os.listdir(sourceDir)
        children.sort()
        for child in children:
            if child == "__pycache__":
                continue
            path = os.path.join(sourceDir, child)
            relPath = os.path.join(relDir, child)
            if os.path.isdir(path):
                strings.append('        <Filter Name="%s">\n' % (child))
                VS2008._def_files(path, relPath, strings)
                strings.append('        </Filter>\n')
            else:
                strings.append('        <File RelativePath="%s" />\n' % (path))


    def _emit_vcproj(self, projName, variants):
        firstProj = next(iter(variants.values()))
        (_projName, vsProjGuid, vsProjPath) = _get_project_data(firstProj, self.projExt, self.codeBrowsingDir)
        ninjaDir = os.path.dirname(self.projectMan.ninjaPath)
        strings = []

        # create a sorted list of variants by name, so that the output is deterministic
        sortedVariants = sorted(variants.keys(), key = lambda variant: str(variant))

        strings.append(r'''<?xml version="1.0" encoding="Windows-1252"?>
<VisualStudioProject
    ProjectType="Visual C++"
    Version="9.00"
    Name="%s"
    ProjectGUID="{%s}"
    Keyword="MakeFileProj"
    TargetFrameworkVersion="196613" >
    <Platforms>
''' % (projName, vsProjGuid))

        strings.append(r'''        <Platform Name="%s" />%s''' % ("Win32", "\n"))

        strings.append(r'''    </Platforms>
    <ToolFiles>
    </ToolFiles>
    <Configurations>
''')

        for variant in sortedVariants:
            proj = variants[variant]
            strings.append(VS2008._def_config(str(variant), ninjaDir, proj.outputPath, proj))
        strings.append(VS2008._def_config("all", ninjaDir, projName, None))

        strings.append(
r'''    </Configurations>
    <Files>
''')
        VS2008._def_files(proj.projectDir, ".\\", strings)
        strings.append(r'''    </Files>
</VisualStudioProject>
''')

        vsProjContents = "".join(strings)
        io.write_file_if_different(vsProjPath, vsProjContents)
        return (projName, str(vsProjGuid).upper(), vsProjPath)

    def emit_vs_projects(self):
        vsProjList = []
        allVariantNames = set()
        for projName in sorted(self.projectMan._projects.keys()):
            variants = self.projectMan._projects[projName]

            # ignore non-C++ projects
            firstProj = next(iter(variants.values()))
            if not isinstance(firstProj, cpp.CppProject):
                continue

            variantNames = set()
            for variant in variants:
                variantNames.add(str(variant))
                allVariantNames.add(str(variant))

            vsProjInfo = self._emit_vcproj(projName, variants)
            vsProjList.append(vsProjInfo)
        slnPath = os.path.join(self.codeBrowsingDir, "all" + self.slnBaseName)
        _emit_sln(self.slnVer, vsProjList, slnPath, allVariantNames)


class VS2010(VSGenerator):
    def __init__(self, projectMan, codeBrowsingDir = None):
        super().__init__()
        self.projectMan = projectMan
        self.slnVer = "11.00"
        self.slnBaseName = "_vs2010.sln"
        self.projExt = ".vcxproj"
        if codeBrowsingDir:
            self.codeBrowsingDir = codeBrowsingDir
        else:
            self.codeBrowsingDir = os.path.dirname(projectMan.ninjaPath)

    def _def_project_configuration(strings, variantName):
        strings.append('    <ProjectConfiguration Include="%s|Win32">\n' % (variantName))
        strings.append('      <Configuration>%s</Configuration>\n' % (variantName))
        strings.append('      <Platform>Win32</Platform>\n')
        strings.append('    </ProjectConfiguration>\n')

    def _def_config_props(variantName, ninjaDir, targetName, proj):
        defines = ""
        includePaths = ""
        forceIncludes = ""
        if proj and getattr(proj, "set_cpp_compile_options", None):
            task = cpp.CppTask(proj, "dummy", "dummy.o", proj.projectDir)
            proj.set_cpp_compile_options(task)
            defines = ";".join(task.defines)
            includePaths = ";".join(task.includePaths)
            forceIncludes = task.usePCH if task.usePCH else ""
        config = \
r'''  <PropertyGroup Condition="'$(Configuration)|$(Platform)'=='{0}|Win32'">
    <NMakeOutput>{6}</NMakeOutput>
    <NMakeBuildCommandLine>SET VS_UNICODE_OUTPUT=
SET NINJA_STATUS=[%%s/%%t - %%e]
cd {1}
ninja {2}
</NMakeBuildCommandLine>
    <NMakeCleanCommandLine>SET VS_UNICODE_OUTPUT=
SET NINJA_STATUS=[%%s/%%t - %%e]
cd {1}
ninja -t clean {2}
</NMakeCleanCommandLine>
    <NMakeReBuildCommandLine>SET VS_UNICODE_OUTPUT=
SET NINJA_STATUS=[%%s/%%t - %%e]
cd {1}
ninja -t clean {2}
ninja {2}
</NMakeReBuildCommandLine>
    <NMakePreprocessorDefinitions>{3}</NMakePreprocessorDefinitions>
    <NMakeIncludeSearchPath>{4}</NMakeIncludeSearchPath>
    <NMakeForcedIncludes>{5}</NMakeForcedIncludes>
  </PropertyGroup>
'''.format(variantName, ninjaDir, targetName, defines, includePaths, forceIncludes, getattr(proj, "outputPath", "o"))
        return config

    def _def_files(sourceDir, relDir, strings):
        children = os.listdir(sourceDir)
        children.sort()
        for child in children:
            if child == "__pycache__":
                continue
            path = os.path.join(sourceDir, child)
            relPath = os.path.join(relDir, child)
            if os.path.isdir(path):
                VS2010._def_files(path, relPath, strings)
            else:
                if _is_source_file(child):
                    strings.append('    <ClCompile Include="%s" />\n' % (path))
                else:
                    strings.append('    <ClInclude Include="%s" />\n' % (path))

    def _emit_vcxproj(self, projName, variants):
        firstProj = next(iter(variants.values()))
        (_projName, vsProjGuid, vsProjPath) = _get_project_data(firstProj, '.vcxproj', self.codeBrowsingDir)
        ninjaDir = os.path.dirname(self.projectMan.ninjaPath)
        strings = []

        # create a sorted list of variants by name, so that the output is deterministic
        sortedVariants = sorted(variants.keys(), key = lambda variant: str(variant))

        strings.append(r'''<?xml version="1.0" encoding="utf-8"?>
<Project DefaultTargets="Build" ToolsVersion="4.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <ItemGroup Label="ProjectConfigurations">
''')
        for variant in sortedVariants:
            VS2010._def_project_configuration(strings, str(variant))
        VS2010._def_project_configuration(strings, "all")

        strings.append(
r'''  </ItemGroup>
  <PropertyGroup Label="Globals">
    <ProjectGuid>{%s}</ProjectGuid>
    <Keyword>MakeFileProj</Keyword>
    <ConfigurationType>Makefile</ConfigurationType>
    <PlatformToolset>v110</PlatformToolset>
  </PropertyGroup>
  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.Default.props" />
  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.props" />
''' % (vsProjGuid))

        for variant in sortedVariants:
            proj = variants[variant]
            strings.append(VS2010._def_config_props(str(variant), ninjaDir, proj.outputPath, proj))
        strings.append(VS2010._def_config_props("all", ninjaDir, projName, None))

        strings.append('  <ItemGroup>\n')
        VS2010._def_files(proj.projectDir, ".\\", strings)
        strings.append('  </ItemGroup>\n')
        strings.append('  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.targets" />\n')
        strings.append('</Project>\n')

        vsProjContents = "".join(strings)
        io.write_file_if_different(vsProjPath, vsProjContents)
        return (projName, str(vsProjGuid).upper(), vsProjPath)


    def emit_vs_projects(self):
        if self._projectsEmitted:
            return
        self._projectsEmitted = True

        vsProjList = []
        allVariantNames = set()
        for projName in sorted(self.projectMan._projects.keys()):
            variants = self.projectMan._projects[projName]

            # ignore non-C++ projects
            firstProj = next(iter(variants.values()))
            if not isinstance(firstProj, cpp.CppProject):
                continue

            variantNames = set()
            for variant in variants:
                variantNames.add(str(variant))
                allVariantNames.add(str(variant))

            vsProjInfo = self._emit_vcxproj(projName, variants)
            vsProjList.append(vsProjInfo)
        slnPath = os.path.join(self.codeBrowsingDir, "all" + self.slnBaseName)
        _emit_sln(self.slnVer, vsProjList, slnPath, allVariantNames)


class VS2012(VS2010):
    def __init__(self, projectMan, codeBrowsingDir = None):
        super().__init__(projectMan, codeBrowsingDir)
        self.slnVer = "12.00"
        self.slnBaseName = "_vs2012.sln"
