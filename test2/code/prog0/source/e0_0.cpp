#include <stdio.h>
#include "a0_special.h"
#include "a1.h"

int main()
{
    int val;

    val = a0_0();
    val += a0_0_special();
    val += a0_1();
    val += a1_0();
    printf("val = %d\n", val);
    return 0;
}

