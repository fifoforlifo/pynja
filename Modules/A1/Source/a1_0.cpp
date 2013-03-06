#ifdef _WIN32
__declspec(dllexport)
#else
__attribute__((visibility("default")))
#endif
int a1_0()
{
    long long x = 2;
    return x;
}

