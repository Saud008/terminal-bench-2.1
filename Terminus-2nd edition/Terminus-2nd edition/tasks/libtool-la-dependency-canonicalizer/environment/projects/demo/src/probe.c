#include <stdio.h>
#include "api.h"

int main(void) {
    printf("probe:%d\n", core_value());
    return 0;
}
