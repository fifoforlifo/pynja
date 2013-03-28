#ifdef FOO
int a0_0()
{
    int extra = 0;
#ifdef _WIN32
    // NOTE: this is bad practice, relying on PCH for OS headers ...
    // but it's being used to test whether PCH build drivers are working.
    extra = (GetTickCount() - GetTickCount());
#endif
    return 3 + extra;
}
#endif
