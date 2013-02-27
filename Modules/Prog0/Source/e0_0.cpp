#include <stdio.h>
#include "A0_special.h"

int main()
{
    int val;

    val = a0_0();
    val += a0_0_special();
    printf("val = %d\n", val);
    return 0;
}

