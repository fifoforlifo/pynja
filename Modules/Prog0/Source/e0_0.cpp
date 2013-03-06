#include <stdio.h>
#include "A0_special.h"
#include "A1.h"

int main()
{
    int val;

    val = a0_0();
    val += a0_0_special();
    val += a1_0();
    printf("val = %d\n", val);
    return 0;
}

