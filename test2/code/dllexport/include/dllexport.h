#pragma once

#ifdef _WIN32
    #define DLL_EXPORT_11 __declspec(dllexport)
    #define DLL_EXPORT_10 __declspec(dllimport)
    #define DLL_EXPORT_00
    #define DLL_LOCAL_11
    #define DLL_LOCAL_10
    #define DLL_LOCAL_00
#else
    #define DLL_EXPORT_11 __attribute__((visibility("default")))
    #define DLL_EXPORT_10 __attribute__((visibility("default")))
    #define DLL_EXPORT_00
    #define DLL_LOCAL_1  __attribute__((visibility("hidden")))
    #define DLL_LOCAL_0
#endif

#define DLL_EXPORT_SE_I(isLibShared_, isExport_) DLL_EXPORT_ ## isLibShared_ ## isExport_
#define DLL_EXPORT_SE(isLibShared_, isExport_) DLL_EXPORT_SE_I(isLibShared_, isExport_)
#define DLL_EXPORT(name_) DLL_EXPORT_SE(name_ ## _SHARED, name_ ## _EXPORT)

#define DLL_LOCAL_SE_I(isLibShared_) DLL_LOCAL_ ## isLibShared_
#define DLL_LOCAL_SE(isLibShared_) DLL_LOCAL_SE_I(isLibShared_)
#define DLL_LOCAL(name) DLL_LOCAL_SE(name_ ## _SHARED)
