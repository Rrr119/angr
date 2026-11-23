#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int main(void) {
    unsigned int a = 0, b = 0, c = 0, d = 0;
    unsigned int e = 0, f = 0;
    int sink = 0;
    unsigned char buf[16];
    if (read(0, buf, sizeof(buf)) <= 0) return 1;
    a = (buf[0] << 8) | buf[1];
    b = (buf[2] << 8) | buf[3];
    c = (buf[4] << 8) | buf[5];
    d = (buf[6] << 8) | buf[7];
    if (b >= 34) {
    if (d < 38) {
    if (c < 19) {
    sink = 11 % 7;
    } else {
    sink = 17 % 7;
    }
    } else {
    if ((c - 11) != 33) {
    sink = 17 % 7;
    } else {
    sink = 23 % 7;
    }
    }
    } else {
    if (b <= 51) {
    if (a == 25) {
    sink = 17 % 7;
    } else {
    sink = 23 % 7;
    }
    } else {
    if ((c * 14) < 28) {
    sink = 23 % 7;
    } else {
    sink = 29 % 7;
    }
    }
    }

    printf("%d\n", sink);
    return 0;
}
